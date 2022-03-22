# -*- coding: utf-8 -*-
# @author: mkaay

from __future__ import absolute_import, unicode_literals

from future import standard_library

from pyload.core.manager.base import BaseManager

standard_library.install_aliases()


class RemoteManager(BaseManager):

    available = ['WebSocketBackend']

    def setup(self):
        self.backends = []

    def start(self):
        host = self.pyload.config.get('rpc', 'host')
        port = self.pyload.config.get('rpc', 'port')

        for b in self.available:
            klass = getattr(
                __import__('pyload.rpc.{0}'.format(b.lower()),
                           globals(), locals(), [b.lower()], -1), b
            )
            backend = klass(self)
            if not backend.check_deps():
                continue
            try:
                backend.setup(host, port)
                self.pyload.log.info(
                    self._('Starting {0}: {1}:{2}').format(b, host, port))
            except Exception as exc:
                self.pyload.log.error(
                    self._('Failed loading backend {0}').format(
                        b))
                self.pyload.log.error(exc, exc_info=self.pyload.debug)
            else:
                backend.start()
                self.backends.append(backend)

            port += 1
