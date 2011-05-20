'''
Copyright 2011 Acknack Ltd

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

'''
Handles all requests coming from the wave interface
'''
import logging

import config
import emailInterface
import gadgetHandler
from dbtools import settingsTools
from dbtools import sessionTools
from dbtools import waveTools
from permission import rawTypes as pt_raw
from security import sessionCreation
import utils

from waveapi import appengine_robot_runner
from waveapi import element
from waveapi import events
from waveapi import robot

from waveto import waveletTools

from google.appengine.ext import deferred

mrray = None

def OnSelfAdded(event, wavelet):
    '''
    Called when a robot is added to wave.
    Adds the add email participants gadget to the wave
    @param event: the event that triggered
    @param wavelet: the wavelet where the event triggered
    '''
    if not wavelet.robot_address == config.ROBOT_EMAIL:
        logging.info('Proxy_robot- request ignored')
        return
    logging.info('OnSelfAdded')

    #If there is no title add one
    if len(wavelet.title) == 0:
        wavelet.title = "(Untitled)"

    #Add the gadget
    root_blip = waveletTools.getRootBlip(wavelet)
    if root_blip:
        participants_gadget = element.Gadget(config.ADD_PARTICIPANTS_GADGET_URL2,
                                            gadgetHandler.constructInitialState(wavelet))
        participants_gadget.waveid = wavelet.wave_id
        root_blip.at(len(wavelet.title)).insert_after(participants_gadget)

def OnGadgetStateChanged(event, wavelet):
    '''
    Called when a gadget changes state
    Checks the add email participants gadget for new participants
    @param event: the event that triggered
    @param wavelet: the wavelet where the event triggered
    '''
    if not wavelet.robot_address == config.ROBOT_EMAIL:
        logging.info('Proxy_robot- request ignored')
        return
    if wavelet.participants.get_role(config.ROBOT_EMAIL) == wavelet.participants.ROLE_READ_ONLY:
        logging.info("Mr-Ray is read only- request ignored")
        return
    logging.info('OnGadgetStateChanged')

    blip = event.blip
    add_participants_gadget_v2 = blip.first(element.Gadget, url=config.ADD_PARTICIPANTS_GADGET_URL2)
    if(add_participants_gadget_v2):
        gadgetHandler.onUserChangesSettings(event, wavelet, add_participants_gadget_v2)
    add_participants_gadget_v1 = blip.first(element.Gadget, url=config.ADD_PARTICIPANTS_GADGET_URL1)
    if(add_participants_gadget_v1):
        gadgetHandler.onAddParticipantsChangedV1(event, wavelet, add_participants_gadget_v1)

def OnBlipSubmitted(event, wavelet):
    '''
    Called when a new blip is submitted
    Sends emails out if their status' are read
    @param event: the event that triggered
    @param wavelet: the wavelet where the event triggered
    '''
    if not wavelet.robot_address == config.ROBOT_EMAIL:
        logging.info('Proxy_robot- request ignored')
        return
    logging.info('OnBlipSubmitted')
    
    updateUsers(event, wavelet)

def OnParticpantsChanged(event, wavelet):
    '''
    Called when the waves participants change. This will request the gadget
    refetches the waves participant profiles
    '''
    if not wavelet.robot_address == config.ROBOT_EMAIL:
        logging.info('Proxy_robot- request ignored')
        return
    if wavelet.participants.get_role(config.ROBOT_EMAIL) == wavelet.participants.ROLE_READ_ONLY:
        logging.info("Mr-Ray is read only- request ignored")
        return
    logging.info("OnParticipantsChanged")
    
    root_blip = waveletTools.getRootBlip(wavelet)
    if root_blip:
        add_participants_gadget_v2 = root_blip.first(element.Gadget, url=config.ADD_PARTICIPANTS_GADGET_URL2)
        if(add_participants_gadget_v2):
            gadgetHandler.requestParticipantProfilesUpdate(add_participants_gadget_v2)

def updateUsers(event, wavelet):
    '''
    Loops through the users in the wave and sends email if these are the first
    new changes
    @param event: the event that triggered
    @param wavelet: the wavelet where the event triggered
    '''
    blip_id = None
    if event.blip:
        blip_id = event.blip.blip_id
    sessions = sessionTools.fetch(wavelet.wave_id, wavelet.wavelet_id)
    for userSession in sessions:
        if sessionTools.isPublic(userSession):
            continue
        #Dispatch e-mail if these are new changes
        userSettings = settingsTools.get(userSession)
        if userSettings and not userSettings.unseen_changes and not userSettings.rw_permission == pt_raw.RW['DELETED']:
            deferred.defer( emailInterface.sendNotificationEmail,
                            sessionCreation.regenerateUser( wavelet.wave_id,
                                                            wavelet.wavelet_id,
                                                            userSession.email   ),
                            wavelet.wave_id,
                            wavelet.wavelet_id,
                            userSession.email,
                            event.modified_by,
                            wavelet.title)
            settingsTools.markUnseenChanges(session=userSession)

        #Update each users blip unread status
        settingsTools.blipChanges(blip_id, session=userSession)


def ProfileHandler(name):
    '''
    Deals with the profile so that different users have different avatars and
    names
    @param name: the robot name
    '''
    if name == None:
        return {'name'      : 'Mr-Ray',
                'imageUrl'  : config.ROBOT_WEB + 'web/media/icon.png',
                'profileUrl': config.ROBOT_PROFILE_URL}
    else:
        if(utils.isProxyForPublic(name)):
            return {'name'      : utils.getNameFromPublicProxyFor(name) + ' (Mr-Ray Public)',
                    'imageUrl'  : config.ROBOT_WEB + 'web/media/icon_public.png',
                    'profileUrl': config.ROBOT_PROFILE_URL}
        else:
            return {'name'      : utils.getEmailFromProxyFor(name) + ' (Mr-Ray)',
                    'imageUrl'  : config.ROBOT_WEB + 'web/media/icon_proxyfor.png',
                    'profileUrl': config.ROBOT_PROFILE_URL}



if __name__=='__main__':
    logging.info("Creating robot")
    mrray = robot.Robot("Mr-Ray")
    
    mrray.register_handler(events.WaveletSelfAdded, OnSelfAdded, context="ROOT")
    mrray.register_handler(events.GadgetStateChanged, OnGadgetStateChanged, context="SELF")
    mrray.register_handler(events.BlipSubmitted, OnBlipSubmitted, context="SELF")
    mrray.register_handler(events.WaveletParticipantsChanged, OnParticpantsChanged, context="ROOT")
    mrray.register_profile_handler(ProfileHandler)
    
    appengine_robot_runner.run(mrray, debug=True)
