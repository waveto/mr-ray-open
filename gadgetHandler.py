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
Methods that handle the interaction between gadgets and robot
'''
import base64
import logging

import config
from dbtools import sessionTools
from dbtools import settingsTools
from dbtools import waveTools
import emailInterface
from permission import rawTypes as pt_raw
from security import sessionCreation
import utils

from waveapi import simplejson

from google.appengine.api import mail
from google.appengine.ext import deferred


def onUserChangesSettings(event, wavelet, add_gadget):
    '''
    Deals with version two of the add participants gadget changing. Changes
    public settings etc
    @param event: the event that triggered the gadget state change
    @param wavelet: the wavelet the gadget lives in
    @param add_gadget: the add participants gadget retrieved from the wave
    '''
    logging.info("Gadget state changed (v2)")
    gadgetWrapper = addParticipantsGadgetWrapper(add_gadget)
    
    #Process incoming requests
    incomingRequests = gadgetWrapper.getIncomingRequests()
    logging.info("Found " + str(len(incomingRequests)) + " requests")
    for user, request in incomingRequests.items():
        action = request.get("action", None)
        if action == "addEmail":
            _addEmailUser(event, wavelet, gadgetWrapper, user, request)
        elif action == "deleteEmail":
            _deleteEmailUser(wavelet, gadgetWrapper, user, request)
        elif action == "changePublic":
            _changePublicSettings(wavelet, gadgetWrapper, user, request)
    
    #Process incoming participant profiles
    _saveParticipantProfiles(wavelet, gadgetWrapper)
    
    #Write changes back to gadget
    gadgetWrapper.reconstructGadgetState()

def _saveParticipantProfiles(wavelet, gadgetWrapper):
    '''
    Saves the participant profiles state to the datastore
    @param wavelet: the wavelet with the gadget
    @param gadgetWrapper: the object wrapping the gadgets state
    '''
    if gadgetWrapper.getParticipantDetailsState() == "updated":
        participantDetails = gadgetWrapper.getParticipantDetails()
        waveMeta = waveTools.createOrUpdate(    wavelet.wave_id,
                                                wavelet.wavelet_id,
                                                participant_profiles=participantDetails)
        gadgetWrapper.setParticipantDetailsState(None)
    
def _addEmailUser(event, wavelet, gadgetWrapper, user, request):
    '''
    Adds an email particpant to the wave and updates the gadget to reflect
    @param event: the event that triggered the changed gadget
    @param wavelet: the wavelet where the request originated from
    @param user: the user that made the request
    @param gadgetWrapper: the object that wraps this gadgets state
    @param request: the request to process
    '''
    logging.info("Add email user request")
    email = request.get('params').get("email") or None
    message = request.get('params').get('message') or ""
    
    if email:
        logging.info("Creating new session for " + email)
        url = sessionCreation.generateNewUser(  wavelet.wave_id,
                                                wavelet.wavelet_id,
                                                email,
                                                pt_raw.RW['READ_WRITE'])
        deferred.defer(
            emailInterface.sendFirstNotificationEmail,
            url,
            wavelet.wave_id,
            wavelet.wavelet_id,
            email,
            event.modified_by,
            wavelet.title,
            message=message)

        wavelet.add_proxying_participant(utils.getProxyForFromEmail(email))
        gadgetWrapper.addEmailParticipant(email)
        gadgetWrapper.deleteIncomingRequest(user)
    
def _deleteEmailUser(wavelet, gadgetWrapper, user, request):
    '''
    Removes an email participant from the wave and updates the gadget to reflect
    @param wavelet: the wavelet where the request originated from
    @param user: the user that made the request
    @param gadgetWrapper: the object that wraps this gadgets state
    @param request: the request to process
    '''
    logging.info("Delete email user request")
    email = request.get('params').get("email") or None
    if email:
        logging.info("Deleting " + email)
        settingsTools.changeRWPermission(   pt_raw.RW['DELETED'],
                                            key={   'wave_id'   :   wavelet.wave_id,
                                                    'wavelet_id':   wavelet.wavelet_id,
                                                    'email'     :   email})
        gadgetWrapper.removeEmailParticipant(email)
        gadgetWrapper.deleteIncomingRequest(user)


def _changePublicSettings(wavelet, gadgetWrapper, user, request):
    '''
    Changes the public settings for the wave and updates the gadget to reflect
    @param wavelet: the wavelet where the request originated from
    @param user: the user that made the request
    @param gadgetWrapper: the object that wraps this gadgets state
    @param request: the request to process
    '''
    logging.info("Change public settings request")
    #Extract values from the incoming json
    isPublic = None
    isReadOnly = None
    params = request.get("params", None)
    if params:
        isPublic = params.get("isPublic", None)
        isReadOnly = params.get("isReadOnly", None)
    if isPublic == None:
        isPublic = False
    if isReadOnly == None:
        isReadOnly = True
    
    #Convert values into permissions
    if isReadOnly:
        rw_permission = pt_raw.RW['READ']
    else:
        rw_permission = pt_raw.RW['READ_WRITE']
    if not isPublic:
        rw_permission = pt_raw.RW['DELETED']
    url = sessionCreation.generateNewUser(  wavelet.wave_id,
                                            wavelet.wavelet_id,
                                            config.PUBLIC_EMAIL,
                                            rw_permission)
    gadgetWrapper.changePublicSettings(isPublic, isReadOnly, url)
    gadgetWrapper.deleteIncomingRequest(user)
        
    
def constructInitialState(wavelet):
    '''
    Constructs the initial gadget state. This is used purely for migration from
    the v1 gadget to v2 gadget. So it returns a list of email users in the 
    correct format for the gadget
    @param wavelet: the wavelet where the gadget will live
    @return a dictionary containing the key values of the initial state
    '''
    sessions = sessionTools.fetch(wavelet.wave_id, wavelet.wavelet_id)
    #Form the email list
    email_list = []
    public_session = None
    for session in sessions:
        if sessionTools.isPublic(session):
            public_session = session
        else:
            email_list.append(session.email)
            
    #Form public settings
    public = {}
    isPublic = False
    isReadOnly = True
    
    try:
        public_settings = settingsTools.get(public_session)
        rw_permission = public_settings.rw_permission
        
        if rw_permission == pt_raw.RW['READ']:
            isPublic = True
            isReadOnly = True
        elif rw_permission == pt_raw.RW['READ_WRITE']:
            isPublic = True
            isReadOnly = False
    except:
        #Just means public settings could not be found. Defaults will be used
        pass
    public.update({'isPublic' : isPublic, 'isReadOnly' : isReadOnly});
    
    output = base64.b64encode(simplejson.dumps({'emailParticipants' : email_list,
                                                'public'            : public}))
    return {'state' : output, 'participantDetailsState' : 'fetch'}

def requestParticipantProfilesUpdate(add_gadget):
    '''
    Sends a request to the gadget to resend the participant profiles
    @param add_gadget: the gadget found in this wave
    '''
    add_gadget.update_element({'participantDetailsState' : 'fetch'})

def onAddParticipantsChangedV1(event, wavelet, add_gadget):
    '''
    Deals with the add participants gadget changing, subscribes wave users etc
    @param event: the event that triggered the gadget state change
    @param wavelet: the wavelet the gadget lives in
    @param add_gadget: the add participants gadget retrieved from the wave
    '''

    #Fetch the values from the gadget
    participants_json = add_gadget.get("EMAIL-PARTICIPANTS", None)
    if participants_json:
        participants_json = base64.b64decode(participants_json)
    else:
        participants_json = "[]"
    participants = simplejson.loads(participants_json)
    new_participant = add_gadget.get("ADD-PARTICIPANT", None)

    if new_participant:
        logging.info("Subscribing new e-mail user: " + new_participant)
        #Check the email address appears valid. Fail silently if not. The js
        #should check and report errors before sending. This prevents hackers
        if not mail.is_email_valid(new_participant):
            logging.info(new_participant + " not subscribed. E-mail address not valid")
            return

        #Only update if the user is new
        if not new_participant in participants:
            deferred.defer(
                    emailInterface.sendFirstNotificationEmail,
                    sessionCreation.generateNewUser(wavelet.wave_id,
                                                    wavelet.wavelet_id,
                                                    new_participant,
                                                    pt_raw.RW['READ_WRITE']),
                    wavelet.wave_id,
                    wavelet.wavelet_id,
                    new_participant,
                    event.modified_by,
                    wavelet.title)

            participants.append(new_participant)
            wavelet.add_proxying_participant(utils.getProxyForFromEmail(new_participant))

        #Update the gadget
        participants_json = simplejson.dumps(participants)
        add_gadget.update_element({ "ADD-PARTICIPANT": None,
                                    "EMAIL-PARTICIPANTS": base64.b64encode(participants_json)})


class addParticipantsGadgetWrapper:
    '''
    Object that models the add participants gadget in a pythonic way
    '''
    def __init__(self, gadget):
        '''
        @param gadget: the gadget instance
        '''
        self._gadget = gadget
        self._default_state = {"emailParticipants" : [], 'public':{'isPublic':False, 'isReadOnly':True}}
        self._parseGadgetState()
    
    def _loads(self, obj):
        '''
        Loads an object from the gadget state if it is b64/json
        @param obj: the raw string to load
        @return the python object
        '''
        if not obj:
            return None
        return simplejson.loads(base64.b64decode(obj))
    
    def _dumps(self, obj):
        '''
        Writes an object to a string so it can be stored in the gadget state
        @param obj: the object to write to string
        @return a b64/json string representing the object
        '''
        if not obj:
            return ""
        return base64.b64encode(simplejson.dumps(obj))
    
    def _parseGadgetState(self):
        '''
        Parses the state variable into a python data structure and stores in
        the object
        '''
        self._participantDetails = self._loads(self._gadget.get("participantDetails", None)) or {}
        self._state = self._loads(self._gadget.get("state", None)) or {}
        self._participantDetailsState = self._gadget.get("participantDetailsState", None)
        self._parseIncomingRequests()
    
    def _parseIncomingRequests(self):
        '''
        Parses the incoming requests and stores in the object
        '''
        commands = {}
        for command in self._gadget.keys():
            if command == "participantDetails" or command == "participantDetailsState" or command == "state":
                continue
            commands.update({command : self._loads(self._gadget.get(command, None))})
        self._requests = commands
    
    def getParticipantDetails(self):
        '''
        @return partipantDetails object or {} if it is not present
        '''
        return self._participantDetails or {}
    
    def getParticipantDetailsState(self):
        '''
        @return participantDetailsState variable or None if it is not present
        '''
        return self._participantDetailsState
    
    def setParticipantDetailsState(self, state):
        '''
        @param state: the new participantDetailsState variable or None to delete
        '''
        self._participantDetailsState = state
    
    def addEmailParticipant(self, email):
        '''
        @param email: the email address to add
        '''
        if not self._state:
            self._state = self._default_state
        self._state['emailParticipants'].append(email)
            
    
    def removeEmailParticipant(self, email):
        '''
        @param email: the email address to remove
        '''
        if self._state:
            if email in self._state['emailParticipants']:
                self._state['emailParticipants'].remove(email)
        else:
            self._state = self._default_state
    
    def changePublicSettings(self, isPublic, isReadOnly, url):
        '''
        @param isPublic: the public state T/F
        @param isReadOnly: the readOnlyState T/F
        @param url: the public url
        '''
        if self._state:
            self._state['public']['isPublic'] = isPublic
            self._state['public']['isReadOnly'] = isReadOnly
            self._state['public']['url'] = url
        else:
            self._state = {"emailParticipants" : [], 'public':{'isPublic':isPublic, 'isReadOnly':isReadOnly}}
    
    def getIncomingRequests(self):
        '''
        @return the incoming requests object or {} if not present
        '''
        return self._requests
    
    def deleteIncomingRequest(self, key):
        '''
        @param key: the key to remove
        '''
        self._requests[key] = None
    
    def reconstructGadgetState(self):
        '''
        Reconstructs the gadgets state so it can be re-written to the gadget
        '''
        update = {  "state"                     : self._dumps(self._state),
                    "participantDetailsState"   : self._participantDetailsState}
        for key in self._requests:
            update.update({key: self._requests[key]})
        self._gadget.update_element(update)
