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
A set of generic configuration variables used throughout the system
'''
#Robot web configuration/details
ROBOT_IDENT= "mr-ray-open"
ROBOT_PROFILE_URL = "https://github.com/waveto/mr-ray-open"
ROBOT_DOMAIN = "appspot.com"
ROBOT_EMAIL_DOMAIN = "appspotmail.com"
ROBOT_EMAIL = ROBOT_IDENT + "@" + ROBOT_DOMAIN
ROBOT_EMAIL_SEND_NOTIFICATION = "noreply-notification@" + ROBOT_IDENT + "." + ROBOT_EMAIL_DOMAIN
ROBOT_EMAIL_SENDER_NAME = "Mr Ray open the Wav-e-mail bot"
ROBOT_WEB = "http://" + ROBOT_IDENT + "." + ROBOT_DOMAIN + "/"

#Oauth configuration

#(Default config for mr-ray)
if ROBOT_IDENT == "mr-ray-open":
    CONSUMER_KEY = "YOUR CONSUMER KEY"
    CONSUMER_SECRET = "YOUR CONSUMER SECRET"

if ROBOT_IDENT == "mr-ray-open-test":
    #(Default config for mr-ray-test)
    CONSUMER_KEY = "YOUR CONSUMER SECRET"
    CONSUMER_SECRET = "YOUR CONSUMER SECRET"

WAVE_SERVER_RPC = "http://gmodules.com/api/rpc"

#Gadgets
ADD_PARTICIPANTS_GADGET_URL1 = ROBOT_WEB + "web/gadget/addparticipants.xml"
ADD_PARTICIPANTS_GADGET_URL2 = ROBOT_WEB + "web/gadget/addparticipantsv2.xml"


#Proxy for participants
PROXY_FOR_AT_REPLACE = "-_at_-"

#Contacting external wave service
HTTP_LOSSY_RETRY = 2
HTTP_IMPORTANT_RETRY = 4

#Public users
PUBLIC_EMAIL = "mrrayopen-public@wave.to"
