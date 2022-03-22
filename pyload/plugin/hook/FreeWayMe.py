﻿# -*- coding: utf-8 -*-

from pyload.plugin.internal.MultiHook import MultiHook


class FreeWayMe(MultiHook):
    __name    = "FreeWayMe"
    __type    = "hook"
    __version = "0.15"

    __config = [("pluginmode"    , "all;listed;unlisted", "Use for plugins"                     , "all"),
                  ("pluginlist"    , "str"                , "Plugin list (comma separated)"       , ""   ),
                  ("revertfailed"  , "bool"               , "Revert to standard download if fails", True ),
                  ("reload"        , "bool"               , "Reload plugin list"                  , True ),
                  ("reloadinterval", "int"                , "Reload interval in hours"            , 12   )]

    __description = """FreeWay.me hook plugin"""
    __license     = "GPLv3"
    __authors     = [("Nicolas Giese", "james@free-way.me")]


    def getHosters(self):
        # Get account data
        if not self.account or not self.account.canUse():
           hostis = self.getURL("https://www.free-way.me/ajax/jd.php", get={"id": 3}).replace("\"", "").strip()
        else:
           self.logDebug("AccountInfo available - Get HosterList with User Pass")
           (user, data) = self.account.selectAccount()
           hostis = self.getURL("https://www.free-way.me/ajax/jd.php", get={"id": 3, "user": user, "pass": data['password']}).replace("\"", "").strip()

        self.logDebug("hosters: %s" % hostis)
        return [x.strip() for x in hostis.split(",") if x.strip()]
