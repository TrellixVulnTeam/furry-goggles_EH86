# -*- coding: utf-8 -*-

from pyload.plugin.Account import Account
from pyload.utils import json_loads


class RPNetBiz(Account):
    __name    = "RPNetBiz"
    __type    = "account"
    __version = "0.12"

    __description = """RPNet.biz account plugin"""
    __license     = "GPLv3"
    __authors     = [("Dman", "dmanugm@gmail.com")]


    def loadAccountInfo(self, user, req):
        # Get account information from rpnet.biz
        res = self.getAccountStatus(user, req)
        try:
            if res['accountInfo']['isPremium']:
                # Parse account info. Change the trafficleft later to support per host info.
                account_info = {"validuntil": float(res['accountInfo']['premiumExpiry']),
                                "trafficleft": -1, "premium": True}
            else:
                account_info = {"validuntil": None, "trafficleft": None, "premium": False}

        except KeyError:
            # handle wrong password exception
            account_info = {"validuntil": None, "trafficleft": None, "premium": False}

        return account_info


    def login(self, user, data, req):
        # Get account information from rpnet.biz
        res = self.getAccountStatus(user, req)

        # If we have an error in the res, we have wrong login information
        if 'error' in res:
            self.wrongPassword()


    def getAccountStatus(self, user, req):
        # Using the rpnet API, check if valid premium account
        res = req.load("https://premium.rpnet.biz/client_api.php",
                            get={"username": user, "password": self.getAccountData(user)['password'],
                                 "action": "showAccountInformation"})
        self.logDebug("JSON data: %s" % res)

        return json_loads(res)
