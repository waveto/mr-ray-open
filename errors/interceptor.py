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
Decorator to intercept exceptions and handle them nicely
'''
import logging

import friendlyCodes as eCodes
import output as eOutput
import rayExceptions

from waveto import waveRpc

from waveapi import simplejson

from google.appengine.runtime import DeadlineExceededError

class interceptExceptions(object):
    '''
    Decorator to process exceptions that can be recovered from. If an
    exception is raised the appropriate page or error code is returned to the
    user
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
            try:
                return function(*args, **kwargs)
            except DeadlineExceededError:
                logging.warn("Deadline Exceeded for request")
                if self.render_page:
                    return eOutput.DeadlineExceeded(handler).RenderPage(eCodes.REQUEST_DEADLINE_ERR)
                else:
                    return eOutput.DeadlineExceeded(handler).ReturnResponse()
            except waveRpc.DownloadException:
                logging.warn("Could not download wave from google servers")
                if self.render_page:
                    return eOutput.WaveRpcDownloadProblem(handler).RenderPage(eCodes.CANNOT_CONNECT_TO_WAVE_ERR)
                else:
                    return eOutput.WaveRpcDownloadProblem(handler).ReturnResponse()
            except waveRpc.NotParticipantException:
                logging.warn("Mr-Ray not participant of wave")
                if self.render_page:
                    return eOutput.RayNotWaveParticipant(handler).RenderPage(eCodes.BOT_NOT_PARTICIPANT_ERR)
                else:
                    return eOutput.RayNotWaveParticipant(handler).ReturnResponse()
            except simplejson.decoder.JSONDecodeError:
                logging.warn("Could not decode incoming json")
                return eOutput.JsonDecodingProblem(handler).ReturnResponse()
            except rayExceptions.MalformedRequest:
                logging.warn("The request was malformed in some way")
                return eOutput.MalformedRequest(handler).ReturnResponse()
            except Exception, ex:
                logging.exception("Unknown error")
                if self.render_page:
                    return eOutput.UnknownProblem(handler).RenderPage(eCodes.UNKNOWN_ERR)
                else:
                    return eOutput.UnknownProblem(handler).ReturnResponse()
        return decorated_function