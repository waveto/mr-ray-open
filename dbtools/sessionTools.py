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
Methods to make using Session models easier
'''
import base64

import config
import dbmigration
import memcacheConfig
from models import Session

from waveapi import simplejson

from google.appengine.api import memcache

def fetch(wave_id, wavelet_id):
    '''
    Uses memcache or the datastore to get fetch sessions by wave_id and
    wavelet_id
    @param wave_id: the id of the session to fetch
    @param wavelet_id: the if of the session to fetch
    
    @return the sessions using the most efficient means possible or None if it
    couldn't be found
    '''
    key = base64.b64encode( memcacheConfig.PREFIX['SESSION'] + 
                            wave_id + wavelet_id)
    sessions = memcache.get(key)
    if not sessions == None:
        dbmigration.migratev1tov2(sessions)
        return sessions
    else:
        query = Session.all()
        query.filter("wave_id =", wave_id)
        query.filter("wavelet_id =", wavelet_id)
        sessions = query.fetch(100)
        dbmigration.migratev1tov2(sessions)
        memcache.add(key, sessions, time=memcacheConfig.DEFAULT_EXPIRE_SECS)
        return sessions

def get(wave_id, wavelet_id, email):
    '''
    Uses memcache or the datastore to fetch a single session by wave_id,
    wavelet_id and email
    @param wave_id: the id of the session to fetch
    @param wavelet_id: the id of the session to fetch
    @param email: the email of the session to fetch
    
    @return the session using the most efficient means possible or None if it
    couldn't be found
    '''
    key = base64.b64encode( memcacheConfig.PREFIX['SESSION'] + 
                            wave_id + wavelet_id + email)
    session = memcache.get(key)
    if not session == None:
        dbmigration.migratev1tov2([session])
        return session
    else:
        query = Session.all()
        query.filter("wave_id =", wave_id)
        query.filter("wavelet_id =", wavelet_id)
        query.filter("email =", email)
        session = query.get()
        dbmigration.migratev1tov2([session])
        memcache.add(key, session, time=memcacheConfig.DEFAULT_EXPIRE_SECS)
        return session

def put(session):
    '''
    Saves the session to the datastore and removes it from memcache
    @param session: the session to save
    '''
    session.put()
    memcache.delete(base64.b64encode(   memcacheConfig.PREFIX['SESSION'] +
                                        session.wave_id +
                                        session.wavelet_id))
    memcache.delete(base64.b64encode(   memcacheConfig.PREFIX['SESSION'] +
                                        session.wave_id + 
                                        session.wavelet_id +
                                        session.email))

def isPublic(session):
    '''
    @param session: a session object to test
    @return True if the session is a public session.
    '''
    return session.email == config.PUBLIC_EMAIL