# -*- coding: utf-8 -*-

import datetime
import hashlib
import time

from pyload.plugin.Account import Account
from pyload.utils import json_loads


class RapideoPl(Account):
    __name = "RapideoPl"
    __version = "0.01"
    __type = "account"
    __description = "Rapideo.pl account plugin"
    __license = "GPLv3"
    __authors = [("goddie", "dev@rapideo.pl")]

    _api_url = "http://enc.rapideo.pl"

    _api_query = {
        "site": "newrd",
        "username": "",
        "password": "",
        "output": "json",
        "loc": "1",
        "info": "1"
    }

    _req = None
    _usr = None
    _pwd = None


    def loadAccountInfo(self, name, req):
        self._req = req
        try:
            result = json_loads(self.runAuthQuery())
        except Exception:
            #@TODO: return or let it be thrown?
            return

        premium = False
        valid_untill = -1
        if "expire" in result.keys() and result['expire']:
            premium = True
            valid_untill = time.mktime(datetime.datetime.fromtimestamp(int(result['expire'])).timetuple())

        traffic_left = result['balance']

        return ({
                    "validuntil": valid_untill,
                    "trafficleft": traffic_left,
                    "premium": premium
                })


    def login(self, user, data, req):
        self._usr = user
        self._pwd = hashlib.md5(data['password']).hexdigest()
        self._req = req
        try:
            response = json_loads(self.runAuthQuery())
        except Exception:
            self.wrongPassword()

        if "errno" in response.keys():
            self.wrongPassword()
        data['usr'] = self._usr
        data['pwd'] = self._pwd


    def createAuthQuery(self):
        query = self._api_query
        query['username'] = self._usr
        query['password'] = self._pwd

        return query


    def runAuthQuery(self):
        data = self._req.load(self._api_url, post=self.createAuthQuery())

        return data
