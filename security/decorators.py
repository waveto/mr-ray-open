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
Collection of security decorators used to authenticate/deny etc
'''
import cgi
import logging
import urllib

from dbtools import sessionTools
from dbtools import settingsTools
from errors import friendlyCodes as eCodes
from errors import output as eOutput
from permission.readWrite import rwPermission

from waveapi import simplejson

class isAuthenticated(object):
    '''
    Decorator to authenticate the user. If the user is authenticated allows
    the called method to be executed. If not returns an error
    @param function: the function to call
    @return the function to return
    
    @condition: the first arg must be the webapp.RequestHandler instance
    '''
    def __init__(self, render_page):
        '''
        @param render_page: set to true if this method is rendering a page,
        false if it is answering an ajax call
        '''
        self.render_page = render_page
    
    def __call__(self, function):
        def decorated_function(*args, **kwargs):
            handler = args[0]
            credentials = getAuthenticationValuesFromRequest(handler)
            session = sessionTools.get( credentials['wave_id'],
                                        credentials['wavelet_id'],
                                        credentials['email'])
            if session and session.auth_token == credentials['auth']:
                logging.info("Request authenticated")
                return function(*args, **kwargs)
            else:
                logging.info("Request not authenticated")
                if self.render_page:
                    return eOutput.AuthenticationDenied(handler).RenderPage(eCodes.PERMISSION_DENIED_ERR)
                else:
                    return eOutput.AuthenticationDenied(handler).ReturnResponse()
        return decorated_function

class hasPermission(object):
    '''
    Decorator to authenticate that the user has permission to use this
    resource. If not returns an error.
    @param function: the function to call
    @return the function to return
    
    @condition: the first arg must be the webapp.RequestHandler instance
    '''
    def __init__(self, render_page, permission_required):
        '''
        @param render_page: set to true if this method is rendering a page,
        false if it is answering an ajax call
        @param permission_required: the raw permission level required to access
        this resource
        '''
        self.render_page = render_page
        self.permission_required = permission_required
    
    def __call__(self, function):
        def decorated_function(*args, **kwargs):
            handler = args[0]
            settings = self.getSettings(handler)
            if settings:
                permission = rwPermission(settings.rw_permission)
                if permission.permissionForResource(self.permission_required):
                    return function(*args, **kwargs)
                else:
                    if permission.isDeleted():
                        return self.returnDeletedError(handler)
                    else:
                        return self.returnInadequatePermission(handler)
            return self.returnUnknownError(handler)
        return decorated_function
    
    def getSettings(self, handler):
        '''
        Fetches the settings object for this user
        @param handler: the webapp handler
        @return the settings object or None if it could not be found
        '''
        credentials = getAuthenticationValuesFromRequest(handler)
        session = sessionTools.get( credentials['wave_id'],
                                    credentials['wavelet_id'],
                                    credentials['email'])
        if session:
            settings = settingsTools.get(session)
            if settings:
                return settings
        return None
    
    def returnUnknownError(self, handler):
        '''
        @param handler: the webapp handler
        @return an unkown error page/response to the user
        '''
        logging.info("Unknown error while checking the users permission")
        if self.render_page:
            return eOutput.UnknownProblem(handler).RenderPage(eCodes.UNKNOWN_ERR)
        else:
            return eOutput.UnknownProblem(handler).ReturnResponse()
    
    def returnDeletedError(self, handler):
        '''
        @param handler: the webapp handler
        @return a deleted error page/response to the user
        '''
        logging.info("User has been deleted from this resource")
        if self.render_page:
            return eOutput.UserDeleted(handler).RenderPage(eCodes.USER_DELETED_ERR)
        else:
            return eOutput.UserDeleted(handler).ReturnResponse()
    
    def returnInadequatePermission(self, handler):
        '''
        @param handler: the webapp handler
        @return an inadewuatePermission error page/response to the user
        '''
        logging.info("User has inadequate permission rights")
        if self.render_page:
            return eOutput.InadequatePermission(handler).RenderPage(eCodes.INADEQUATE_PERMISSION_ERR)
        else:
            return eOutput.InadequatePermission(handler).ReturnResponse()

def getAuthenticationValuesFromRequest(requestHandler):
    '''
    Fetches the wave id, wavelet id, email and auth token from the request
    handler using whichever means are possible. If they cannot be found
    returns an empty string for each
    @param requestHandler: the request object to extract the values from
    @return a dict containing {wave_id, wavelet_id, email, auth}
    '''
    
    #Load the json if it is available
    try:
        json = simplejson.loads(cgi.escape(requestHandler.request.body))
    except:
        json = {}

    #Take either the values from the url or from the json
    return {
    "wave_id"   : requestHandler.request.get("waveid", urllib.unquote(json.get("waveid", ""))),
    "wavelet_id": requestHandler.request.get("waveletid", urllib.unquote(json.get("waveletid", ""))),
    "email"     : requestHandler.request.get("email", urllib.unquote(json.get("email", ""))),
    "auth"      : requestHandler.request.get("auth", urllib.unquote(json.get("auth", "")))
    }