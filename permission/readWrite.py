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
Wrapper to model a read write permission in a pythonic way
'''
import rawTypes

class rwPermission:
    '''
    Wrapper class for a raw permission providing a more pythonic way to model
    the permissions infrastructure
    '''
    
    _raw_permission = None
    
    def __init__(self, raw_permission):
        '''
        @param raw_permission: the raw permission to wrap
        '''
        self._raw_permission = raw_permission
    
    def getRawPermission(self):
        '''
        @return the raw permission
        '''
        return self._raw_permission
    
    def canRead(self):
        '''
        @return true only if the user can read the item
        '''
        if self._raw_permission == rawTypes.RW['READ'] or self._raw_permission == rawTypes.RW['READ_WRITE']:
            return True
        return False
    
    def canWrite(self):
        '''
        @return true only if the user can write to the item
        '''
        return self._raw_permission == rawTypes.RW['READ_WRITE']
    
    def isDeleted(self):
        '''
        @return true only if the user has been deleted/removed from this item
        '''
        return self._raw_permission == rawTypes.RW['DELETED']
    
    def permissionForResource(self, compareTo):
        '''
        Compares the given permission to the permission type of this object.
        If the user has permission to access the resource then true is returned
        @param compareTo: a raw permission type
        @return True if and only if the permission type is higher than the given
        '''
        if self.isDeleted():
            return False
        if compareTo == rawTypes.RW['READ'] and not self.canRead():
            return False
        if compareTo == rawTypes.RW['READ_WRITE'] and not self.canWrite():
            return False
        return True
        