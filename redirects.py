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
Redirects user to different pages
'''
import cgi
import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

class RedirectWaveToMrRay(webapp.RequestHandler):

    def get(self):
        '''
        Redirects a user to wave.to/projects/mr-ray/
        '''
        self.redirect("http://wave.to/projects/mr-ray/", permanent=True)




if __name__=="__main__":
    run_wsgi_app(   webapp.WSGIApplication(
                                            [('/', RedirectWaveToMrRay)]
    ))
