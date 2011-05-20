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
Methods used for migrating database models between versions
'''
from models import Settings
import settingsTools
import sessionTools

from waveapi import simplejson

def migratev1tov2(sessions):
    '''
    Looks at the provided session and if it is running version 1 migrates it
    to version 2
    @param session: the sessions to potentially migrate
    '''
    for session in sessions:
        if session and session.version == 1:
            settings = Settings(read_blips      = simplejson.loads(session.read_blips or '[]'),
                                unseen_changes  = session.unseenChanges,
                                parent          = session,
                                key_name        = settingsTools.generateKey(session.wave_id,
                                                                            session.wavelet_id,
                                                                            session.email))
            settingsTools.put(settings, session.wave_id, session.wavelet_id, session.email)
            session.version = 2
            session.read_blips = None
            session.unseenChanges = None
            sessionTools.put(session)