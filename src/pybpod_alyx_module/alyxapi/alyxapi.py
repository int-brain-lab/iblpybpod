import requests

from pybpod_alyx_module import settings as settingspy_conf
from pybpod_alyx_module.alyxapi.data.data import Data
from pybpod_alyx_module.alyxapi.subjects.subjects import Subjects


class AlyxAPI():

    def __init__(self):
        self._logged = False
        self.subjects = Subjects(self)
        self.data = Data(self)
        self.addr = settingspy_conf.ALYX_PLUGIN_ADDRESS
        #self.serveraddr = 'http://alyx.champalimaud.pt:8000'
        #self.auth_endpoint = '/auth-token/'

    def login(self, _username, _password):
        _data = dict(username = _username,password = _password)
        result = requests.post(self.addr+'/auth-token',data=_data)
        if result.ok:
            token = result.json()
            
            self.headers = {
                'Authorization': 'Token {}'.format(list(token.values())[0]),
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            }
            return True
        return False

    def getusers(self):
        result = requests.get(self._addr+'/users',self.headers)


    def getaddr(self):
        return self.addr

    def setaddr(self,value):
        self.addr = value


