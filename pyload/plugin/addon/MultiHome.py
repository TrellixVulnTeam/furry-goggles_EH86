# -*- coding: utf-8 -*-

import time

from pyload.plugin.Addon import Addon


class MultiHome(Addon):
    __name    = "MultiHome"
    __type    = "addon"
    __version = "0.12"

    __config = [("interfaces", "str", "Interfaces", "None")]

    __description = """Ip address changer"""
    __license     = "GPLv3"
    __authors     = [("mkaay", "mkaay@mkaay.de")]


    def setup(self):
        self.register   = {}
        self.interfaces = []

        self.parseInterfaces(self.getConfig('interfaces').split(";"))

        if not self.interfaces:
            self.parseInterfaces([self.config.get("download", "interface")])
            self.setConfig("interfaces", self.toConfig())


    def toConfig(self):
        return ";".join(i.adress for i in self.interfaces)


    def parseInterfaces(self, interfaces):
        for interface in interfaces:
            if not interface or str(interface).lower() == "none":
                continue
            self.interfaces.append(Interface(interface))


    def activate(self):
        requestFactory = self.core.requestFactory
        oldGetRequest = requestFactory.getRequest


        def getRequest(pluginName, account=None):
            iface = self.bestInterface(pluginName, account)
            if iface:
                iface.useFor(pluginName, account)
                requestFactory.iface = lambda: iface.adress
                self.logDebug("Using address", iface.adress)
            return oldGetRequest(pluginName, account)

        requestFactory.getRequest = getRequest


    def bestInterface(self, pluginName, account):
        best = None
        for interface in self.interfaces:
            if not best or interface.lastPluginAccess(pluginName, account) < best.lastPluginAccess(pluginName, account):
                best = interface
        return best


class Interface(object):

    def __init__(self, adress):
        self.adress = adress
        self.history = {}


    def lastPluginAccess(self, pluginName, account):
        if (pluginName, account) in self.history:
            return self.history[(pluginName, account)]
        return 0


    def useFor(self, pluginName, account):
        self.history[(pluginName, account)] = time.time()


    def __repr__(self):
        return "<Interface - %s>" % self.adress
