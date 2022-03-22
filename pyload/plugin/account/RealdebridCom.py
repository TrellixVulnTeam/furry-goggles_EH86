# -*- coding: utf-8 -*-

import xml.dom.minidom as dom

from pyload.plugin.Account import Account


class RealdebridCom(Account):
    __name    = "RealdebridCom"
    __type    = "account"
    __version = "0.45"

    __description = """Real-Debrid.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("Devirex Hazzard", "naibaf_11@yahoo.de")]


    def loadAccountInfo(self, user, req):
        if self.pin_code:
            return {"premium": False}
        html = req.load("https://real-debrid.com/api/account.php")
        xml = dom.parseString(html)
        account_info = {"validuntil": float(xml.getElementsByTagName("expiration")[0].childNodes[0].nodeValue),
                        "trafficleft": -1}

        return account_info


    def login(self, user, data, req):
        self.pin_code = False
        html = req.load("https://real-debrid.com/ajax/login.php",
                        get={"user": user, "pass": data['password']},
                        decode=True)

        if "Your login informations are incorrect" in html:
            self.wrongPassword()

        elif "PIN Code required" in html:
            self.logWarning(_("PIN code required. Please login to https://real-debrid.com using the PIN or disable the double authentication in your control panel on https://real-debrid.com"))
            self.pin_code = True
