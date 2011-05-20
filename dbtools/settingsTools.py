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
Methods to make using Settings models easier
'''
import base64

import dbConfig
import memcacheConfig
from models import Settings
import sessionTools

from google.appengine.api import memcache
from google.appengine.ext import db

def generateKey(wave_id, wavelet_id, email):
    '''
    Generates a key for a settings tuple
    @param wave_id: the wave id of the parent
    @param wavelet_id: the wavelet id of the parent
    @param email: the email of the parent
    @return the key that can be used for this tuple
    '''
    return dbConfig.KEY_PREFIX["SETTINGS"] + wave_id + "|" + wavelet_id + "|" + email

def get(session):
    '''
    Uses memcache or the datastore to fetch a single setting by wave_id,
    wavelet_id and email. Ideally this should fetch session only if needed but
    this wouldn't work with the appengine transaction framework.
    @transaction_safe
    @param session: the parent session object

    @return the setting using the most efficient means possible or None if it
    couldn't be found
    '''
    if not session:
        return None
    key = base64.b64encode( memcacheConfig.PREFIX['SETTINGS'] + 
                            session.wave_id + 
                            session.wavelet_id +
                            session.email)
    setting = memcache.get(key)
    if not setting == None:
        return setting
    else:
        query = Settings.all()
        query.ancestor(session)
        setting = query.get()
        memcache.add(key, setting, time=memcacheConfig.DEFAULT_EXPIRE_SECS)
        return setting

def put(setting, wave_id, wavelet_id, email):
    '''
    Saves the setting to the datastore and removes it from memcache
    @transaction_safe
    @param setting: the setting to save
    @param wave_id: the wave id of the settings parent
    @param wavelet_id: the wavelet id of the settings parent
    @param email: the email of the settings parent
    '''
    setting.put()
    memcache.delete(base64.b64encode(   memcacheConfig.PREFIX['SETTINGS'] +
                                        wave_id + 
                                        wavelet_id +
                                        email))

def markSeenChanges(key=None, session=None):
    '''
    Marks that a user has seen changes in a wave. Supply one of the optional
    arguments. Supplying session is always more efficient if you already have
    the value
    @param key=None: a dict containing wave_id, wavelet_id and email
    @param session=None: the parent session object
    '''
    if not key == None:
        _updateUnseenChanges(   key['wave_id'],
                                key['wavelet_id'],
                                key['email'],
                                False,
                                None)
    elif not session == None:
        _updateUnseenChanges(   session.wave_id,
                                session.wavelet_id,
                                session.email,
                                False,
                                session)
    
    

def markUnseenChanges(key=None, session=None):
    '''
    Marks that a user has seen new unseen changes in a wave. Supply one of the
    optional arguments. Supplying session is always more efficient if you
    already have the value
    @param key=None: a dict containing wave_id, wavelet_id and email
    @param session=None: the parent session object
    '''
    if not key == None:
        _updateUnseenChanges(   key['wave_id'],
                                key['wavelet_id'],
                                key['email'],
                                True,
                                None)
    elif not session == None:
        _updateUnseenChanges(   session.wave_id,
                                session.wavelet_id,
                                session.email,
                                True,
                                session)
    

def _updateUnseenChanges(wave_id, wavelet_id, email, value, session):
    '''
    Changes the value of unseen_changes in a nice transaction safe way
    @param wave_id: the wave id of the session to modify
    @param wavelet_id: the wavelet id of the session to modify
    @param email: the email of the session to modify
    @param value: the new value for unseen_changes
    @param session: if provided uses given session, if None fetches from db
    '''
    if session == None:
        session = sessionTools.get(wave_id, wavelet_id, email)

    def worker(session, wave_id, wavelet_id, email, value):
        '''
        @transaction_safe
        '''
        settings = get(session)
        if settings:
            settings.unseen_changes = value
            put(settings, wave_id, wavelet_id, email)

    db.run_in_transaction(worker, session, wave_id, wavelet_id, email, value)

def userReadsBlip(blip_id, key=None, session=None):
    '''
    Marks a single blip read for this user. Supply one of the optional
    arguments. Supplying session is always more efficient if you
    already have the value
    @param key=None: a dict containing wave_id, wavelet_id and email
    @param session=None: the parent session object
    @param blip_id: the blip that is to be marked read
    '''
    if session == None:
        session = sessionTools.get(key['wave_id'], key['wavelet_id'], key['email'])     

    def worker(session, blip_id):
        '''
        @transaction_safe
        '''
        settings = get(session)
        if settings:
            if not blip_id in settings.read_blips:
                settings.read_blips.append(blip_id)
                put(settings, session.wave_id, session.wavelet_id, session.email)

    db.run_in_transaction(worker, session, blip_id)

def blipChanges(blip_id, key=None, session=None):
    '''
    Marks a single blip unread for this user. Supply one of the optional
    arguments. Supplying session is always more efficient if you
    already have the value
    @param key=None: a dict containing wave_id, wavelet_id and email
    @param session=None: the parent session object
    @param blip_id: the blip that is to be marked read
    '''
    if blip_id == None:
        return
    if session == None:
        session = sessionTools.get(key['wave_id'], key['wavelet_id'], key['email'])     

    def worker(session, blip_id):
        '''
        @transaction_safe
        '''
        settings = get(session)
        if settings:
            if blip_id in settings.read_blips:
                settings.read_blips.remove(blip_id)
                put(settings, session.wave_id, session.wavelet_id, session.email)

    db.run_in_transaction(worker, session, blip_id)

def changeRWPermission(new_permission, key=None, session=None):
    '''
    Changes the RW permission for this session. Supply one of the optional
    arguments. Supplying session is always more efficient if you already have
    the value.
    @param key=None: a dict containing wave_id, wavelet_id and email
    @param session=None: the parent session object
    @param new_permission: the raw permission type to give this session
    '''
    if session == None:
        session = sessionTools.get(key['wave_id'], key['wavelet_id'], key['email'])
    
    def worker(session, new_permission):
        '''
        @transaction_safe
        '''
        settings = get(session)
        settings.rw_permission = new_permission
        put(settings, session.wave_id, session.wavelet_id, session.email)

    db.run_in_transaction(worker, session, new_permission)
    