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
Collection of classes that write out error pages or error codes
'''
import os

import config

from google.appengine.ext.webapp import template

class AuthenticationDenied:
    
    def __init__(self, handler):
        '''
        @param handler: the request handler for to return the error through
        '''
        self.handler = handler

    def RenderPage(self, error_code):
        '''
        Renders a page that informs the user the page could not be found or
        that validation failed
        @param error_code: the error code to add to the page
        '''
        self.handler.response.clear()
        path = os.path.join(os.path.dirname(__file__), '../templates/denied.html')
        self.handler.response.out.write(template.render(path, {'robot_web': config.ROBOT_WEB, 'error_code': error_code}))
        self.handler.response.set_status(401)

    def ReturnResponse(self):
        '''
        Returns the response code that indicates the user is not authorized
        to view this page
        '''
        self.handler.response.clear()
        self.handler.response.set_status(401)

class WaveRpcDownloadProblem:

    def __init__(self, handler):
        '''
        @param handler: the request handler for to return the error through
        '''
        self.handler = handler

    def RenderPage(self, error_code):
        '''
        Renders a page that informs the user the page could not be found or
        that validation failed
        @param error_code: the error code to add to the page
        '''
        self.handler.response.clear()
        path = os.path.join(os.path.dirname(__file__), '../templates/cantcontactwave.html')
        self.handler.response.out.write(template.render(path, {'robot_web': config.ROBOT_WEB, 'error_code': error_code}))
        self.handler.response.set_status(502)

    def ReturnResponse(self):
        '''
        Returns the response code that indicates the user is not authorized
        to view this page
        '''
        self.handler.response.clear()
        self.handler.response.set_status(502)

class RayNotWaveParticipant:

    def __init__(self, handler):
        '''
        @param handler: the request handler for to return the error through
        '''
        self.handler = handler

    def RenderPage(self, error_code):
        '''
        Renders a page that informs the user the page could not be found or
        that validation failed
        @param error_code: the error code to add to the page
        '''
        self.handler.response.clear()
        path = os.path.join(os.path.dirname(__file__), '../templates/robotremoved.html')
        self.handler.response.out.write(template.render(path, {'robot_web': config.ROBOT_WEB, 'error_code': error_code}))
        self.handler.response.set_status(403)

    def ReturnResponse(self):
        '''
        Returns the response code that indicates the user is not authorized
        to view this page
        '''
        self.handler.response.clear()
        self.handler.response.set_status(403)

class DeadlineExceeded:

    def __init__(self, handler):
        '''
        @param handler: the request handler for to return the error through
        '''
        self.handler = handler

    def RenderPage(self, error_code):
        '''
        Renders a page that informs the user the page could not be found or
        that validation failed
        @param error_code: the error code to add to the page
        '''
        self.handler.response.clear()
        path = os.path.join(os.path.dirname(__file__), '../templates/standarderror.html')
        self.handler.response.out.write(template.render(path, {'robot_web': config.ROBOT_WEB, 'error_code': error_code}))
        self.handler.response.set_status(503)

    def ReturnResponse(self):
        '''
        Returns the response code that indicates the user is not authorized
        to view this page
        '''
        self.handler.response.clear()
        self.handler.response.set_status(503)

class UnknownProblem:

    def __init__(self, handler):
        '''
        @param handler: the request handler for to return the error through
        '''
        self.handler = handler

    def RenderPage(self, error_code):
        '''
        Renders a page that informs the user the page could not be found or
        that validation failed
        @param error_code: the error code to add to the page
        '''
        self.handler.response.clear()
        path = os.path.join(os.path.dirname(__file__), '../templates/standarderror.html')
        self.handler.response.out.write(template.render(path, {'robot_web': config.ROBOT_WEB, 'error_code': error_code}))
        self.handler.response.set_status(500)

    def ReturnResponse(self):
        '''
        Returns the response code that indicates the user is not authorized
        to view this page
        '''
        self.handler.response.clear()
        self.handler.response.set_status(500)

class JsonDecodingProblem:

    def __init__(self, handler):
        '''
        @param handler: the request handler for to return the error through
        '''
        self.handler = handler

    def ReturnResponse(self):
        '''
        Returns the response code that indicates the user is not authorized
        to view this page
        '''
        self.handler.response.clear()
        self.handler.response.set_status(400)

class InadequatePermission:

    def __init__(self, handler):
        '''
        @param handler: the request handler for to return the error through
        '''
        self.handler = handler

    def RenderPage(self, error_code):
        '''
        Renders a page that informs the user the page could not be found or
        that validation failed
        @param error_code: the error code to add to the page
        '''
        self.handler.response.clear()
        path = os.path.join(os.path.dirname(__file__), '../templates/inadequatepermission.html')
        self.handler.response.out.write(template.render(path, {'robot_web': config.ROBOT_WEB, 'error_code': error_code}))
        self.handler.response.set_status(401)

    def ReturnResponse(self):
        '''
        Returns the response code that indicates the user is not authorized
        to view this page
        '''
        self.handler.response.clear()
        self.handler.response.set_status(401)

class UserDeleted:

    def __init__(self, handler):
        '''
        @param handler: the request handler for to return the error through
        '''
        self.handler = handler

    def RenderPage(self, error_code):
        '''
        Renders a page that informs the user the page could not be found or
        that validation failed
        @param error_code: the error code to add to the page
        '''
        self.handler.response.clear()
        path = os.path.join(os.path.dirname(__file__), '../templates/userdeleted.html')
        self.handler.response.out.write(template.render(path, {'robot_web': config.ROBOT_WEB, 'error_code': error_code}))
        self.handler.response.set_status(403)

    def ReturnResponse(self):
        '''
        Returns the response code that indicates the user is not authorized
        to view this page
        '''
        self.handler.response.clear()
        self.handler.response.set_status(403)

class MalformedRequest:

    def __init__(self, handler):
        '''
        @param handler: the request handler for to return the error through
        '''
        self.handler = handler

    def ReturnResponse(self):
        '''
        Returns the response code that indicates the user is not authorized
        to view this page
        '''
        self.handler.response.clear()
        self.handler.response.set_status(400)