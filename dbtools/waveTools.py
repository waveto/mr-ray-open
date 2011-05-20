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
Methods to make using WaveTools models easier
'''
import base64

import dbConfig
import memcacheConfig
from models import FollowedWave
from models import WaveMeta

from google.appengine.api import memcache

def get(wave_id, wavelet_id):
    '''
    Fetches the WaveMeta object from the datastore using the most efficient
    method
    @param wave_id: the wave id of the tuple
    @param wavelet_id: the wavelet id of the tuple
    @return the WaveMeta object or None if it could not be found
    '''
    followedWave = _getFollowedWave(wave_id, wavelet_id)
    if followedWave == None:
        return None
    return _getWaveMeta(followedWave)

def put(waveMeta, wave_id, wavelet_id):
    '''
    Places the waveMeta into the datastore
    @param waveMeta: the waveMeta object to place
    @param wave_id: the wave id the tuple relates to
    @param wavelet_id: the wavelet id the tuple relates to
    '''
    _putWaveMeta(waveMeta, wave_id, wavelet_id)

def createOrUpdate(wave_id, wavelet_id, participant_profiles=None):
    '''
    Creates or updates a followed wave and wave meta object
    @param wave_id: the id of the wave these records are for
    @param wavelet_id: the id of the wavelet these records are for
    @param participant_profiles=None: the participant profiles for this wave
    '''
    #Fetch or create
    waveMeta = get(wave_id, wavelet_id)
    if not waveMeta:
        followedWave = FollowedWave(wave_id     =   wave_id,
                                    wavelet_id  =   wavelet_id,
                                    key_name    =   _generateFollowedWaveKey(   wave_id,
                                                                                wavelet_id))
        _putFollowedWave(followedWave)
        waveMeta = WaveMeta(parent = followedWave)
    
    if participant_profiles:
        waveMeta.participant_profiles = participant_profiles
    
    put(waveMeta, wave_id, wavelet_id)

def _getFollowedWave(wave_id, wavelet_id):
    '''
    Returns a followed wave if it can be found in the datastore or memcache
    @param wave_id: the wave id of the database entry
    @param wavelet_id: the wavelet id of the database entry
    @return the followed wave instance, or None if it was not found
    '''
    key = base64.b64encode( memcacheConfig.PREFIX['FOLLOWED_WAVE'] + 
                            wave_id + wavelet_id)
    followedWave = memcache.get(key)
    if not followedWave == None:
        return followedWave
    else:
        followedWave = FollowedWave.get_by_key_name(
                                _generateFollowedWaveKey(wave_id, wavelet_id)
                                                    )
        memcache.add(key, followedWave, time=memcacheConfig.DEFAULT_EXPIRE_SECS)
        return followedWave

def _generateFollowedWaveKey(wave_id, wavelet_id):
    '''
    Generates a key for a followed wave instance
    @param wave_id: the id of the wave this model represents
    @param wavelet_id: the id of the wavelet this model represents
    '''
    return dbConfig.KEY_PREFIX["FOLLOWED_WAVE"] + wave_id + "|" + wavelet_id

def _getWaveMeta(followedWave):
    '''
    Returns a wave meta instance if it can be found in the datastore or 
    memcache
    @transaction_safe
    @param followedWave: the parent followedWave instance
    @return the WaveMeta instance or None if it was not found
    '''
    key = base64.b64encode( memcacheConfig.PREFIX['WAVE_META'] + 
                            followedWave.wave_id +
                            followedWave.wavelet_id)
    waveMeta = memcache.get(key)
    if not waveMeta == None:
        return waveMeta
    else:
        query = WaveMeta.all()
        query.ancestor(followedWave)
        waveMeta = query.get()
        memcache.add(key, waveMeta, time=memcacheConfig.DEFAULT_EXPIRE_SECS)
        return waveMeta

def _putFollowedWave(followedWave):
    '''
    Puts the followed wave into the datastore clearing memcache etc
    @param followedWave: the followedWave instance to add to the datastore
    '''
    followedWave.put()
    memcache.delete(base64.b64encode(   memcacheConfig.PREFIX['FOLLOWED_WAVE'] + 
                                        followedWave.wave_id +
                                        followedWave.wavelet_id))

def _putWaveMeta(waveMeta, wave_id, wavelet_id):
    '''
    Puts the WaveMeta into the datastore clearing memcache etc
    @param waveMeta: the waveMeta to place in the datastore
    @param wave_id: the wave_id this tuple relates to
    @param wavelet_id: the wavelet id this tuple relates to
    '''
    waveMeta.put()
    memcache.delete(base64.b64encode(   memcacheConfig.PREFIX['WAVE_META'] + 
                                        wave_id + wavelet_id))

def updateParticipantProfiles(participant_profiles, wave_id, wavelet_id):
    '''
    Updates the participants profiles in the WaveMeta.
    @param participant_profiles: the new participant profiles data to add to 
    the model
    @param wave_id: the wave id of the parent FollowedWave object
    @param wavelet_id: the wavelet id of the parent FollowedWave object
    '''
    followedWave = _getFollowedWave(wave_id, wavelet_id)
    
    def worker(followedWave, participant_profiles):
        '''
        @transaction_safe
        '''
        waveMeta = _getWaveMeta(followedWave)
        waveMeta.participant_profiles = participant_profiles
        _putWaveMeta(waveMeta, followedWave.wave_id, followedWave.wavelet_id)
    
    if not followedWave == None:
        db.run_in_transaction(worker, waveMeta, participant_profiles)