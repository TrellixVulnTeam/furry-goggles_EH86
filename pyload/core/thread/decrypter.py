# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import time

from future import standard_library

from pyload.core.datatype.base import (DownloadStatus, LinkStatus,
                                       ProgressInfo, ProgressType)
from pyload.core.datatype.package import Package
from pyload.core.network.base import Abort, Retry
from pyload.core.thread.plugin import PluginThread
from pyload.utils.misc import accumulate
from pyload.utils.purge import uniquify

standard_library.install_aliases()


class DecrypterThread(PluginThread):
    """Thread for decrypting."""
    __slots__ = ['_progress', 'data', 'error', 'fid', 'pid']

    def __init__(self, manager, data, fid, pid, owner):
        super(DecrypterThread, self).__init__(manager, owner)
        # [...(url, plugin)...]
        self.data = data
        self.fid = fid
        self.pid = pid
        # holds the ProgressInfo, while running
        self.__progress_info = None
        # holds if an error happened
        self.error = False

    def get_progress_info(self):
        return self.__progress_info

    def run(self):
        pack = self.pyload.files.get_package(self.pid)
        api = self.pyload.api.with_user_context(self.owner)
        links, packages = self.decrypt(accumulate(self.data), pack.password)

        # if there is only one package links will be added to current one
        if len(packages) == 1:
            # TODO: also rename the package (optionally)
            links.extend(packages[0].links)
            del packages[0]

        if links:
            self.pyload.log.info(
                self._('Decrypted {0:d} links into package {1}').format(
                    len(links),
                    pack.name))
            api.add_links(self.pid, [l.url for l in links])

        for pack_ in packages:
            api.add_package(pack_.name, pack_.get_urls(), pack.password)

        self.pyload.files.set_download_status(
            self.fid, DownloadStatus.Finished
            if not self.error else DownloadStatus.Failed)
        self.manager.done(self)

    def _decrypt(self, name, urls, password):
        klass = self.pyload.pgm.load_class('crypter', name)
        plugin = None
        result = []

        # updating progress
        self.__progress_info.plugin = name
        self.__progress_info.name = self._('Decrypting {0} links').format(
            len(urls) if len(urls) > 1 else urls[0])

        # TODO: dependency check, there is a new error code for this
        # TODO: decrypting with result yielding
        if not klass:
            self.error = True
            # if err:
            result.extend(
                LinkStatus(
                    url, url, -1, DownloadStatus.NotPossible, name)
                for url in urls)
            self.pyload.log.debug(
                "Plugin '{0}' for decrypting was not loaded".format(name))
            self.__progress_info.done += len(urls)
            return

        try:
            plugin = klass(self.pyload, password)
            try:
                result = plugin._decrypt(urls)
            except Retry:
                time.sleep(1)
                result = plugin._decrypt(urls)
            plugin.log_debug('Decrypted', result)

        except Abort:
            plugin.log_info(self._('Decrypting aborted'))

        except Exception as exc:
            plugin.log_error(self._('Decrypting failed'))
            self.pyload.log.error(exc, exc_info=self.pyload.debug)

            self.error = True
            # generate error linkStatus
            # if err:
            result.extend(LinkStatus(
                url, url, -1, DownloadStatus.Failed, name) for url in urls)

            # no debug for intentional errors
            # if self.pyload.debug and not isinstance(e, Fail):
            # self.pyload.log.error(exc, exc_info=self.pyload.debug)
            # self.debug_report(plugin.__name__, plugin=plugin)
        finally:
            if plugin:
                plugin.clean()
            self.__progress_info.done += len(urls)

        return result

    def decrypt(self, plugin_map, password=None):
        result = []
        self.__progress_info = ProgressInfo(
            'BasePlugin', '', self._('decrypting'), 0, 0, len(
                self.data), self.owner,
            ProgressType.Decrypting
        )
        # TODO: QUEUE_DECRYPT
        result = self._pack_result(
            self._decrypt(name, urls, password) for name,
            urls in plugin_map.items())
        # clear the progress
        self.__progress_info = None
        return result

    def _pack_result(self, result):
        # generated packages
        packs = {}
        # urls without package
        urls = []
        # merge urls and packages
        for packages in result:
            for pack in packages:
                if isinstance(pack, Package):
                    if pack.name in packs:
                        packs[pack.name].urls.extend(pack.urls)
                    elif not pack.name:
                        urls.extend(pack.links)
                    else:
                        packs[pack.name] = pack
                else:
                    urls.append(pack)
        return uniquify(urls), list(packs.values())
