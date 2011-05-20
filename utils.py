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
Collection of commonly widely used methods
'''
import base64

import config
from dbtools import settingsTools
from dbtools import sessionTools
from dbtools import waveTools

from waveapi import simplejson

def getProxyForFromEmail(email):
    '''
    Returns the proxy for name from a given email address
    @param email: the original email address
    
    @return the proxy for email with banned chars stripped
    '''
    return email.replace("@", config.PROXY_FOR_AT_REPLACE)

def getEmailFromProxyFor(proxyfor):
    """
    Returns the users email address from their proxy for name
    @param proxyfor the proxy for email address
    
    @return the original email address
    """
    index = proxyfor.rfind(config.PROXY_FOR_AT_REPLACE)
    if index == -1:
        return proxyfor
    else:
        return proxyfor[0:index] + "@" + proxyfor[index+len(config.PROXY_FOR_AT_REPLACE):len(proxyfor)]

def getProxyForFromPublic(name):
    '''
    Returns the proxy for name from a given public name
    @param name: the users name
    
    @return the proxy for email with banned charachters removed
    '''
    return name.replace("@", "") + "." + config.PUBLIC_EMAIL.replace("@", config.PROXY_FOR_AT_REPLACE)

def isProxyForPublic(proxyfor):
    '''
    Returns true if this represents a public email
    @param email: the email to check
    
    @return true only if this is a public email
    '''
    index = proxyfor.rfind(config.PROXY_FOR_AT_REPLACE)
    if index == -1:
        reformed = proxyfor
    else:
        reformed = proxyfor[0:index] + "@" + proxyfor[index+len(config.PROXY_FOR_AT_REPLACE):len(proxyfor)]
    if reformed.rfind(config.PUBLIC_EMAIL) == -1:
        return False
    return True

def getNameFromPublicProxyFor(proxyfor):
    '''
    Returns the users name from their public email address
    @param proxyfor: the proxy for email
    
    @return the users name
    '''
    index = proxyfor.rfind("." + config.PUBLIC_EMAIL.replace("@", config.PROXY_FOR_AT_REPLACE))
    
    if index == -1:
        return proxyfor
    else:
        return proxyfor[0:index]
    

def construct_wavelet_json_for_http_response(wavelet_data, wave_id, wavelet_id, email, b64Encode=False):
    '''
    Constructs the json that will be sent back through the http request from
    various elements
    @param wavelet_data: the dict with the wavelet and wavelet json
    @param wave_id: the id of the wave
    @param wavelet_id: the id of the wavelet
    @param email: the email of the user waiting for the response
    @param b64Encode=False: set to true if you want the response base64 encoded
    
    @return the json to be sent to the webpage
    '''
    #Fetch the required data from the datastore
    session = sessionTools.get(wave_id, wavelet_id, email)
    settings = settingsTools.get(session)
    waveMeta = waveTools.get(wave_id, wavelet_id)
    if waveMeta:
        participant_profiles = waveMeta.participant_profiles or {}
    else:
        participant_profiles = {}
    
    #Construct the outgoing json
    wavelet_json = {
        'wavelet'       :   wavelet_data.get("json"),
        'readblips'     :   settings.read_blips or [],
        'profiles'      :   participant_profiles,
        'isPublic'      :   sessionTools.isPublic(session),
        'rwPermission'  :   settings.rw_permission   
    }
    if b64Encode:
        return base64.b64encode(simplejson.dumps(wavelet_json))
    else:
        return simplejson.dumps(wavelet_json)