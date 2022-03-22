# -*- coding: utf-8 -*-

from pyload.plugin.Account import Account


class RehostTo(Account):
    __name    = "RehostTo"
    __type    = "account"
    __version = "0.16"

    __description = """Rehost.to account plugin"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org")]


    def loadAccountInfo(self, user, req):
        premium     = False
        trafficleft = None
        validuntil  = -1
        session     = ""

        html = req.load("http://rehost.to/api.php",
                        get={'cmd' : "login", 'user': user,
                             'pass': self.getAccountData(user)['password']})
        try:
            session = html.split(",")[1].split("=")[1]

            html = req.load("http://rehost.to/api.php",
                            get={'cmd': "get_premium_credits", 'long_ses': session})

            if html.strip() == "0,0" or "ERROR" in html:
                self.logDebug(html)
            else:
                traffic, valid = html.split(",")

                premium     = True
                trafficleft = self.parseTraffic(traffic + "MB")
                validuntil  = float(valid)

        finally:
            return {'premium'    : premium,
                    'trafficleft': trafficleft,
                    'validuntil' : validuntil,
                    'session'    : session}


    def login(self, user, data, req):
        html = req.load("http://rehost.to/api.php",
                        get={'cmd': "login", 'user': user, 'pass': data['password']},
                        decode=True)

        if "ERROR" in html:
            self.logDebug(html)
            self.wrongPassword()
