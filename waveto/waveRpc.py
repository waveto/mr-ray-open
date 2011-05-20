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
def retry_fetch_wavelet(retries, robot, wave_id, wavelet_id):
    '''
    Wrapper for fetch_wavelet. Retries a number of times before failing.
    Excepts nicely if a known error is thrown
    @param retries: the number of times to retry the request
    @param robot: the Wave robot object
    @param wave_id: the wave id to attempt to fetch
    @param wavelet_id: the wavelet id to attempt to fetch
    
    @return the wavelet, or if it couldn't be fetched raises an exception
    '''
    excep = None
    for i in range(0, retries):
        try:
            return robot.fetch_wavelet(wave_id, wavelet_id)
        except Exception, e:
            excep = e
            if excep.message.find("is not a participant of wave id") != -1:
                raise NotParticipantException("User is not participant of Wave")

    raise DownloadException("Problem downloading content from Wave server: ".join(excep.args))

def retry_fetch_wavelet_json(retries, robot, wave_id, wavelet_id):
    '''
    Wrapper for fetch_wavelet_json. Retries a number of times before failing
    Excepts nicely if a known error is thrown
    @param retries: the number of times to retry the request
    @param robot: the Wave robot object
    @param wave_id: the wave id to attempt to fetch
    @param wavelet_id: the wavelet id to attempt to fetch
    
    @return the wavelet, or if it couldn't be fetched raises an exception
    '''
    excep = None
    for i in range(0, retries):
        try:
            return robot.fetch_wavelet_json(wave_id, wavelet_id)
        except Exception, e:
            excep = e
            if excep.message.find("is not a participant of wave id") != -1:
                raise NotParticipantException("User is not participant of Wave")

    raise DownloadException("Problem downloading content from Wave server: ".join(excep.args))

def retry_submit(retries, robot, wavelet):
    '''
    Wrapper for submit. Retries a number of times before failing
    Excepts nicely if a known error is thrown
    @param retries: the number of times to retry the request
    @param robot: the Wave robot object
    
    @return the result from robot.submit, or if it couldn't be fetched raises an exception
    '''
    excep = None
    for i in range(0, retries):
        try:
            return robot.submit(wavelet)
        except Exception, e:
            excep = e
            if excep.message.find("is not a participant of wave id") != -1 or excep.message.find("RPC Error500") != -1:
                raise NotParticipantException("User is not participant of Wave")

    raise DownloadException("Problem submitting content to Wave server: ".join(excep.args))


class NotParticipantException(Exception):
    '''
    Indicates that a participant is in the wave
    '''
    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)

class DownloadException(Exception):
    '''
    Indicates that there was an error while downloading the wave content
    '''
    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)