# -*- coding: utf-8 -*-

from pyload.plugin.Account import Account
from pyload.utils import json_loads


class RapidgatorNet(Account):
    __name    = "RapidgatorNet"
    __type    = "account"
    __version = "0.09"

    __description = """Rapidgator.net account plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    API_URL = "http://rapidgator.net/api/user"


    def loadAccountInfo(self, user, req):
        validuntil  = None
        trafficleft = None
        premium     = False
        sid         = None

        try:
            sid = self.getAccountData(user).get('sid')
            assert sid

            html = req.load("%s/info" % self.API_URL, get={'sid': sid})

            self.logDebug("API:USERINFO", html)

            json = json_loads(html)

            if json['response_status'] == 200:
                if "reset_in" in json['response']:
                    self.scheduleRefresh(user, json['response']['reset_in'])

                validuntil  = json['response']['expire_date']
                trafficleft = float(json['response']['traffic_left'])
                premium     = True
            else:
                self.logError(json['response_details'])

        except Exception, e:
            self.logError(e)

        return {'validuntil' : validuntil,
                'trafficleft': trafficleft,
                'premium'    : premium,
                'sid'        : sid}


    def login(self, user, data, req):
        try:
            html = req.load('%s/login' % self.API_URL, post={"username": user, "password": data['password']})

            self.logDebug("API:LOGIN", html)

            json = json_loads(html)

            if json['response_status'] == 200:
                data['sid'] = str(json['response']['session_id'])
                return
            else:
                self.logError(json['response_details'])

        except Exception, e:
            self.logError(e)

        self.wrongPassword()
