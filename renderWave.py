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
Handles requests incoming at /wave and returns the rendered page
'''
import base64
import logging
import os

import config
from dbtools import settingsTools
from errors.interceptor import *
from permission import rawTypes as pt_raw
from security.decorators import *
import utils

from waveto import waveRpc

from waveapi import robot

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

mrray = None

class RenderWavePage(webapp.RequestHandler):

    @isAuthenticated(True)
    @hasPermission(True, pt_raw.RW['READ'])
    @interceptExceptions(True)
    def get(self):
        '''
        Fetches the wavelet and returns the template html
        '''
        logging.info("GET: /wave")

        #Fetch the auth values from the url
        self.wave_id = self.request.get('waveid', "")
        self.wavelet_id = self.request.get("waveletid", "")
        self.email = self.request.get("email", "")
        self.auth_token = self.request.get("auth", "")

        logging.info("Request waveid: " + self.wave_id + " waveletid: " + self.wavelet_id + " email: " + self.email + " auth token: " + self.auth_token)

        wavelet_details = waveRpc.retry_fetch_wavelet_json( config.HTTP_IMPORTANT_RETRY,
                                                            mrray,
                                                            self.wave_id,
                                                            self.wavelet_id)
        settingsTools.markSeenChanges(key={ 'wave_id'   : self.wave_id,
                                            'wavelet_id': self.wavelet_id,
                                            'email'     : self.email})
        wavelet_json = utils.construct_wavelet_json_for_http_response(  wavelet_details,
                                                                        self.wave_id,
                                                                        self.wavelet_id,
                                                                        self.email,
                                                                        b64Encode=True)
        self._renderWavePage(wavelet_json)

    def _renderWavePage(self, wavelet_json):
        '''
        Renders the page with the Mr-Ray view of the wave
        @param wavelet_json: the wavelet json to be included on the webpage
        '''
        template_values = { 'wave_json'             :   wavelet_json,
                            'robot_web'             :   config.ROBOT_WEB,
                            'robot_email'           :   base64.b64encode(config.ROBOT_EMAIL),
                            'robot_ident'           :   config.ROBOT_IDENT,
                            'robot_domain'          :   config.ROBOT_DOMAIN,
                            'proxy_for_at_replace'  :   config.PROXY_FOR_AT_REPLACE,
                            'public_email'          :   base64.b64encode(config.PUBLIC_EMAIL)}
        path = os.path.join(os.path.dirname(__file__), 'templates/renderwave.html')
        self.response.out.write(template.render(path, template_values))



if __name__=="__main__":

    mrray = robot.Robot(config.ROBOT_IDENT)
    mrray.setup_oauth(config.CONSUMER_KEY, config.CONSUMER_SECRET, server_rpc_base=config.WAVE_SERVER_RPC)

    run_wsgi_app(   webapp.WSGIApplication(
                                            [('/wave', RenderWavePage)]
    ))
