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
Database models
'''
from google.appengine.api import datastore_types
from google.appengine.ext import db

from permission import rawTypes as pt_raw

from waveapi import simplejson

class JSONList(db.Property):
    def get_value_for_datastore(self, model_instance):
        value = super(JSONList, self).get_value_for_datastore(model_instance)
        return self._deflate(value)
    def validate(self, value):
        return self._inflate(value)
    def make_value_from_datastore(self, value):
        return self._inflate(value)
    def _inflate(self, value):
        if value is None:
            return []
        if isinstance(value, unicode) or isinstance(value, str):
            return simplejson.loads(str(value))
        return value
    def _deflate(self, value):
        return db.Text(simplejson.dumps(value))
    data_type = datastore_types.Text

class JSONMap(db.Property):
    def get_value_for_datastore(self, model_instance):
        value = super(JSONMap, self).get_value_for_datastore(model_instance)
        return self._deflate(value)
    def validate(self, value):
        return self._inflate(value)
    def make_value_from_datastore(self, value):
        return self._inflate(value)
    def _inflate(self, value):
        if value is None:
            return {}
        if isinstance(value, unicode) or isinstance(value, str):
            return simplejson.loads(str(value))
        return value
    def _deflate(self, value):
        return db.Text(simplejson.dumps(value))
    data_type = datastore_types.Text

class Session(db.Model):
    """
    Model that is used to record the users access token + session data etc
    This is a root type and thus read/writes will not be transactionally safe
    """
    wave_id = db.StringProperty(required=True)
    wavelet_id = db.StringProperty(required=True)
    email = db.StringProperty(required=True)
    auth_token = db.StringProperty(required=True)
    version = db.IntegerProperty(default=1)

    #Depricated fields. DO NOT USE!
    read_blips = db.TextProperty(required=False)
    unseenChanges = db.BooleanProperty(required=False, default=False)

class Settings(db.Model):
    """
    Model that is used to record users session settings
    Settings parent should always be set to a Session so read/writes can be
    transactionally safe
    """
    read_blips = JSONList()
    unseen_changes = db.BooleanProperty(default=False)#Default for migration. Users will get 1 rouge e-mail
    rw_permission = db.StringProperty(required=True, default=pt_raw.RW['READ_WRITE'])#Default for migration when we only had email users with rw permission

class FollowedWave(db.Model):
    """
    Model that is used to record a wave
    This is a root type and thus read/writes will not be transactionally safe
    """
    wave_id = db.StringProperty(required=True)
    wavelet_id = db.StringProperty(required=True)

class WaveMeta(db.Model):
    """
    Model that can hold meta data about a wave
    Parent should always be set to a FollowedWave so read/writes can be
    transactionally safe
    """
    participant_profiles = JSONMap()