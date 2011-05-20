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
Handles requests incoming at wave/action and acts upon them
'''
import cgi
import logging
import re
import urllib

import config
import emailInterface
from errors.rayExceptions import MalformedRequest
from errors.interceptor import *
from permission import rawTypes as pt_raw
from security import sessionCreation
from security.decorators import *
import utils

from dbtools import settingsTools
from dbtools import sessionTools
from waveto import waveRpc

from waveapi import robot
from waveapi import simplejson

from google.appengine.ext import deferred
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

mrray = None

class ActionWave(webapp.RequestHandler):    

    ##########################################################################
    # POST / GET request handlers
    ##########################################################################
    @isAuthenticated(False)
    @interceptExceptions(False)
    def post(self):
        '''
        Handles the incoming post request and performs the relevant action on
        the wave.
        '''
        logging.info("POST: /wave/action/")
        #Fetch the auth values from the url + form values
        incoming_json = cgi.escape(self.request.body)
        self.incoming = simplejson.loads(incoming_json)

        self.wave_id = urllib.unquote(self.incoming.get("waveid", ""))
        self.wavelet_id = urllib.unquote(self.incoming.get("waveletid", ""))
        self.email = urllib.unquote(self.incoming.get("email", ""))
        self.auth_token = self.incoming.get("auth", "")
        self.action = self.incoming.get("action", None)

        logging.info("Request waveid: " + self.wave_id + " waveletid: " + self.wavelet_id + " email: " + self.email + " auth token: " + self.auth_token)

        if self.action == "REPLY":
            return self._replyRequest()
        elif self.action == "READ":
            return self._readRequest()
        elif self.action == "REFRESH":
            return self._refreshRequest()
        else:
            return self._malformedRequest()

    ##########################################################################
    # Request handlers for different request types
    ##########################################################################
    @hasPermission(False, pt_raw.RW['READ_WRITE'])
    def _replyRequest(self):
        '''
        Launches a reply request with ensuring permissions are checked etc
        '''
        logging.info("This is a REPLY request")
        settingsTools.markSeenChanges(key={ 'wave_id'   : self.wave_id,
                                            'wavelet_id': self.wavelet_id,
                                            'email'     : self.email})
        self._UserReplies()
    
    @hasPermission(False, pt_raw.RW['READ_WRITE'])
    def _readRequest(self):
        '''
        Launches a read request ensuring permissions are checked etc
        Note: this endpoint is accessible via public but is never shown on the wave
        '''
        logging.info("This is a READ request")
        settingsTools.markSeenChanges(key={ 'wave_id'   : self.wave_id,
                                            'wavelet_id': self.wavelet_id,
                                            'email'     : self.email})
        self.__UserReads(self.incoming.get('blipid', ""))
        self.response.set_status(201)
    
    @hasPermission(False, pt_raw.RW['READ'])
    def _refreshRequest(self):
        '''
        Launches a refresh request ensuring permissions are checked etc
        '''
        logging.info("This is a REFRESH request")
        self._UserRefresh()
    
    @hasPermission(False, pt_raw.RW['READ'])
    def _malformedRequest(self):
        '''
        Launches a malformed request ensuring permissions are checked etc
        '''
        logging.warn("The requested service " + str(self.action) + " was requested but is not valid")
        raise MalformedRequest("The requested service " + str(self.action) + " was requested but is not valid")


    ##########################################################################
    # Request support methods for carrying out actions
    ##########################################################################
    def _UserReplies(self):
        '''
        Sends a reply to wave from the user along with other tasks such as
        marking the wave read etc.
        '''
        #Modify requirements if the wave is public
        if sessionTools.isPublic(sessionTools.get( self.wave_id, self.wavelet_id, self.email)):
            self._PublicReplies()
        else:
            #Fetch the wavelet and do some house-keeping
            wavelet = waveRpc.retry_fetch_wavelet(  config.HTTP_IMPORTANT_RETRY,
                                                    mrray,
                                                    self.wave_id,
                                                    self.wavelet_id)
        
            try:
                wavelet.robot_address = config.ROBOT_EMAIL
            except:
                pass#The wavelet already has the robot address
            proxy_for = utils.getProxyForFromEmail(self.email)
            
            if wavelet.participants.get_role(config.ROBOT_IDENT + "+" + proxy_for + "@" + config.ROBOT_DOMAIN) == wavelet.participants.ROLE_READ_ONLY:
                #TODO wrong exception raised here
                raise waveRpc.NotParticipantException("Wave permissions do not permit reply")
            if wavelet.participants.get_role(config.ROBOT_EMAIL) == wavelet.participants.ROLE_READ_ONLY:
                #TODO wrong exception raised here
                raise waveRpc.NotParticipantException("Wave permissions do not permit reply")
            
            wavelet.add_proxying_participant(proxy_for)
            self.__InsertBlipIntoWavelet(wavelet, proxy_for)
            self.__AlertEmailParticipants(wavelet, self.email+"(via Mr-Ray)")
            waveRpc.retry_submit(config.HTTP_IMPORTANT_RETRY, mrray, wavelet)

            #Re-fetch the new (updated) wavelet
            new_wavelet_data = waveRpc.retry_fetch_wavelet_json(config.HTTP_IMPORTANT_RETRY,
                                                                mrray,
                                                                self.wave_id,
                                                                self.wavelet_id)
            self.__MarkNewBlipRead(new_wavelet_data)
        
            #Write the response
            wavelet_json = utils.construct_wavelet_json_for_http_response(  new_wavelet_data,
                                                                            self.wave_id,
                                                                            self.wavelet_id,
                                                                            self.email)
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(wavelet_json)
            self.response.set_status(201)
    
    def _PublicReplies(self):
        '''
        Sends a reply to wave from the public user
        Maybe consider merging this into _publicReplies in the future. Methods are very similar
        '''
        self.name = self.incoming.get("name", None)
        if not self.name:
            logger.warn("The response came from a public wave and expected the 'name' field but was not found")
            raise MalformedRequest("The response came from a public wave and expected the 'name' field but was not found")
        if not re.match("^[a-zA-Z0-9_]+$", self.name):
            logger.warn("The response came from a public wave and expected the 'name' field to only contain [a-zA-Z0-9_] but it was " + name)
            raise MalformedRequest("The response came from a public wave and expected the 'name' field to only contain [a-zA-Z0-9_] but it was " + name)
        
        #Fetch the wavelet and do some house-keeping
        wavelet = waveRpc.retry_fetch_wavelet(  config.HTTP_IMPORTANT_RETRY,
                                                mrray,
                                                self.wave_id,
                                                self.wavelet_id)
        
        try:
            wavelet.robot_address = config.ROBOT_EMAIL
        except:
            pass#The wavelet already has the robot address
        proxy_for = utils.getProxyForFromPublic(self.name)
        
        if wavelet.participants.get_role(config.ROBOT_IDENT + "+" + proxy_for + "@" + config.ROBOT_DOMAIN) == wavelet.participants.ROLE_READ_ONLY:
            #TODO wrong exception raised here
            raise waveRpc.NotParticipantException("Wave permissions do not permit reply")
        if wavelet.participants.get_role(config.ROBOT_EMAIL) == wavelet.participants.ROLE_READ_ONLY:
            #TODO wrong exception raised here
            raise waveRpc.NotParticipantException("Wave permissions do not permit reply")
        
        wavelet.add_proxying_participant(proxy_for)
        self.__InsertBlipIntoWavelet(wavelet, proxy_for)
        self.__AlertEmailParticipants(wavelet, self.name + "(via Mr-Ray Public)")
        waveRpc.retry_submit(config.HTTP_IMPORTANT_RETRY, mrray, wavelet)

        #Re-fetch the new (updated) wavelet
        new_wavelet_data = waveRpc.retry_fetch_wavelet_json(config.HTTP_IMPORTANT_RETRY,
                                                            mrray,
                                                            self.wave_id,
                                                            self.wavelet_id)
        
        #Write the response
        wavelet_json = utils.construct_wavelet_json_for_http_response(  new_wavelet_data,
                                                                        self.wave_id,
                                                                        self.wavelet_id,
                                                                        self.email)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(wavelet_json)
        self.response.set_status(201)

    def _UserRefresh(self):
        '''
        Fetches and returns the wavelet json for a user
        '''
        new_wavelet_data = waveRpc.retry_fetch_wavelet_json(config.HTTP_LOSSY_RETRY,
                                                            mrray,
                                                            self.wave_id,
                                                            self.wavelet_id)

        wavelet_json = utils.construct_wavelet_json_for_http_response(  new_wavelet_data,
                                                                        self.wave_id,
                                                                        self.wavelet_id,
                                                                        self.email)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(wavelet_json)



    def __InsertBlipIntoWavelet(self, wavelet, proxy_for):
        '''
        Inserts a blip into the wavelet at the specified position with the
        specified content
        @param wavelet: the wavelet to add the blip to
        @param proxy_for: the proxy_for user to send this request from
        '''
        #Insert blip into the wavelet
        blip_id = self.incoming.get('blipid', "")
        reply = self.incoming.get('reply', '')
        blip = wavelet.blips.get(blip_id, None)
        if(blip == None):
            wavelet.proxy_for(proxy_for).reply().append(reply)
        else:
            blip.proxy_for(proxy_for).reply().append(reply)

    def __AlertEmailParticipants(self, wavelet, who_changed):
        '''
        Send an email out to any other proxy-for participants in the wave
        @param wavelet: the wavelet that the proxy-for participants are
                        subscribed to
        @param who_changed: the friendly name of who changed the wave
        '''
        #Alert other e-mail participants that a new blip has been posted
        sessions = sessionTools.fetch(wavelet.wave_id, wavelet.wavelet_id)

        for userSession in sessions:
            if not userSession.email == self.email and not sessionTools.isPublic(userSession):
                userSettings = settingsTools.get(userSession)
                if not userSettings.unseen_changes and not userSettings.rw_permission == pt_raw.RW['DELETED']:
                    deferred.defer(
                        emailInterface.sendNotificationEmail,
                        sessionCreation.regenerateUser( wavelet.wave_id,
                                                        wavelet.wavelet_id,
                                                        userSession.email   ),
                        wavelet.wave_id,
                        wavelet.wavelet_id,
                        userSession.email,
                        self.email,
                        wavelet.title,
                        who_modified_display=who_changed)
                    
                    settingsTools.markUnseenChanges(session=userSession)

    def __MarkNewBlipRead(self, new_wavelet_data):
        '''
        Marks the new blip as read for the user so they know they have seen it
        already
        @param new_wavelet_data: the new wavelet from the server with the new
                                    blip included
        '''
        #Mark new blip read
        blip_id = self.incoming.get('blipid', "")
        new_parent_blip = new_wavelet_data.get('wavelet').blips.get(blip_id, None)
        if new_parent_blip:
            child_blips = new_parent_blip.child_blips
            for b in child_blips:
                if config.ROBOT_IDENT + "+" + utils.getProxyForFromEmail(self.email) + "@" + config.ROBOT_DOMAIN in b.contributors:
                    self.__UserReads(b.blip_id)


    def __UserReads(self, blip_id):
        '''
        Marks the given blip as read
        @param blip_id: the id of the blip to mark as read
        '''
        if not blip_id:
            return

        #Update the database
        settingsTools.userReadsBlip(blip_id, key={  'wave_id'   : self.wave_id,
                                                    'wavelet_id': self.wavelet_id,
                                                    'email'     : self.email})


if __name__=="__main__":
    logging.info("Creating robot: /wave/action/")

    mrray = robot.Robot(config.ROBOT_IDENT)
    mrray.setup_oauth(config.CONSUMER_KEY, config.CONSUMER_SECRET, server_rpc_base=config.WAVE_SERVER_RPC)

    run_wsgi_app(   webapp.WSGIApplication(
                                            [('/wave/action/', ActionWave)]
    ))
