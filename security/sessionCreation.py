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
Methods which handle generating new users and regenerating auth tokens
'''
import logging
import urllib
import uuid

import config

from dbtools import settingsTools
from dbtools import sessionTools
from dbtools.models import Settings
from dbtools.models import Session


def generateNewUser(wave_id, wavelet_id, email, rw_permission):
    '''
    Generates the database entry for this user and creates the unique url link
    If the user already exists does an overwrite
    @param wave_id: the id of the wave to generate the link for
    @param wavelet_id: the id of the wavelet to generate the link for
    @param email: the email address to generate the link for
    @param rw_permission: the raw read/write permission type this user has
    @return unique url for this user and wave
    '''
    #We don't want duplicates so we need to check for the sesison first. If
    #we do find an existing user we need to apply the default settings
    session = sessionTools.get(wave_id, wavelet_id, email)
    if session:
        logging.info("Found existing user with same credentials. Updating")
        auth_token = session.auth_token
        session.version = 2
        sessionTools.put(session)
        
        settings = settingsTools.get(session)
        if settings:
            settings.unseen_changes = True
            settings.rw_permission = rw_permission
        else:
            settings = Settings(unseen_changes  =   True,
                                rw_permission   =   rw_permission,
                                parent          =   parent,
                                key_name        =   settingsTools.generateKey(  wave_id,
                                                                                wavelet_id,
                                                                                email))
        settingsTools.put(settings, wave_id, wavelet_id, email)
    else:
        auth_token = _generateAuthToken()
        logging.info("Creating new token with auth code " + auth_token)
        session = Session(  wave_id         =   wave_id,
                            wavelet_id      =   wavelet_id,
                            email           =   email,
                            auth_token      =   auth_token,
                            version         =   2)
        sessionTools.put(session)

        settings = Settings(unseen_changes  =   True,
                            rw_permission   =   rw_permission,
                            parent          =   session,
                            key_name        =   settingsTools.generateKey(  wave_id,
                                                                            wavelet_id,
                                                                            email))
        settingsTools.put(settings, wave_id, wavelet_id, email)
    
    return _generateUrl(wave_id, wavelet_id, email, auth_token)
    

def regenerateUser(wave_id, wavelet_id, email):
    '''
    Fetches the database entry for this user and regenerates their unique url
    @param wave_id: the id of the wave to generate the link for
    @param wavelet_id: the id of the wavelet to generate the link for
    @param email: the email address to generate the link for
    @return unique url for this user and wave
    '''
    session = sessionTools.get(wave_id, wavelet_id, email)
    return _generateUrl(session.wave_id,
                        session.wavelet_id,
                        session.email,
                        session.auth_token)

def _generateUrl(wave_id, wavelet_id, email, auth_token):
    '''
    Generates the url for this user
    @param wave_id: the id of the wave to include in the url
    @param wavelet_id: the id of the wavelet to include in the url
    @param email: the email to include in the url
    @param auth_token: the token to include in the url
    
    @return the url for this user
    '''
    args = _generateUrlArguments(   wave_id,
                                    wavelet_id,
                                    email,
                                    auth_token)
    return config.ROBOT_WEB + "wave" + args

def _generateUrlArguments(wave_id, wavelet_id, email, auth_token):
    '''
    Generates the url arguments for the users url
    @param wave_id: the id of the wave to include in the url
    @param wavelet_id: the id of the wavelet to include in the url
    @param email: the email to include in the url
    @param auth_token: the token to include in the url
    
    @return the url arguments for this user
    '''
    arguments = "?"
    arguments += "waveid=" + urllib.quote(wave_id)
    arguments += "&waveletid=" + urllib.quote(wavelet_id)
    arguments += "&email=" + urllib.quote(email)
    arguments += "&auth=" + urllib.quote(auth_token)
    return arguments


def _generateAuthToken():
    '''
    Generates a uniquire auth token
    @return a unique identifier
    '''
    return str(uuid.uuid1().int)
