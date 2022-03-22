# -*- coding: utf-8 -*-
# @author: RaNaN

from __future__ import absolute_import, unicode_literals

from collections import defaultdict
from gettext import gettext
from types import MethodType

from _thread import start_new_thread
from future import standard_library

from pyload.core.datatype.base import (AddonInfo, AddonService,
                                       ServiceDoesNotExist, ServiceException)
from pyload.core.manager.base import BaseManager
from pyload.core.thread import AddonThread
from pyload.utils.layer.legacy.collections import namedtuple
from pyload.utils.layer.safethreading import RLock
from pyload.utils.struct.lock import lock

standard_library.install_aliases()


AddonTuple = namedtuple('AddonTuple', 'instances events handler')


class AddonManager(BaseManager):
    """Manages addons, loading, unloading."""

    def setup(self):
        # TODO: multiuser addons

        # maps plugin names to info tuple
        self.plugins = defaultdict(lambda: AddonTuple([], [], {}))
        # Property hash mapped to meta data
        self.info_props = {}

        self.lock = RLock()
        self.create_index()

        # manage addons on config change
        self.listen_to('config:changed', self.manage_addon)

    def iter_addons(self):
        """Yields (name, meta_data) of all addons."""
        return iter(self.plugins.items())

    @lock
    def call_in_hooks(self, event, event_name, *args):
        """Calls a method in all addons and catch / log errors."""
        for plugin in self.plugins.values():
            for inst in plugin.instances:
                self.call(inst, event, *args)
        self.fire(event_name, *args)

    def call(self, plugin, f, *args):
        try:
            func = getattr(plugin, f)
            return func(*args)
        except Exception as exc:
            plugin.log_error(
                self._('Error when executing {0}'.format(f)))
            self.pyload.log.error(exc, exc_info=self.pyload.debug)

    def invoke(self, plugin, func_name, args):
        """Invokes a registered method."""
        if plugin not in self.plugins and func_name not in self.plugins[
                plugin].handler:
            raise ServiceDoesNotExist(plugin, func_name)

        # TODO: choose correct instance
        try:
            func = getattr(self.plugins[plugin].instances[0], func_name)
            return func(*args)

        except Exception as exc:
            raise ServiceException(exc)

    @lock
    def create_index(self):
        active = []
        deactive = []

        for pluginname in self.pyload.pgm.get_plugins('addon'):
            try:
                # check first for builtin plugin
                attrs = self.pyload.pgm.load_attributes('addon', pluginname)
                internal = attrs.get('internal', False)

                if internal or self.pyload.config.get(
                        pluginname, 'activated'):
                    pluginclass = self.pyload.pgm.load_class(
                        'addon', pluginname)

                    if not pluginclass:
                        continue

                    plugin = pluginclass(self.pyload, self)
                    self.plugins[pluginclass.__name__].instances.append(plugin)

                    # hide internals from printing
                    if not internal and plugin.is_activated():
                        active.append(pluginclass.__name__)
                    else:
                        self.pyload.log.debug(
                            'Loaded internal plugin: {0}'.format(
                                pluginclass.__name__))
                else:
                    deactive.append(pluginname)

            except Exception as exc:
                self.pyload.log.warning(
                    self._('Failed activating {0}').format(pluginname))
                self.pyload.log.error(exc, exc_info=self.pyload.debug)

        self.pyload.log.info(
            self._('Activated addons: {0}').format(', '.join(sorted(active))))
        self.pyload.log.info(self._('Deactivated addons: {0}').format(
            ', '.join(sorted(deactive))))

    def manage_addon(self, plugin, name, value):
        # TODO: multi user

        # check if section was a plugin
        if plugin not in self.pyload.pgm.get_plugins('addon'):
            return

        if name == 'activated' and value:
            self.activate_addon(plugin)
        elif name == 'activated' and not value:
            self.deactivate_addon(plugin)

    @lock
    def activate_addon(self, plugin):
        # check if already loaded
        if plugin in self.plugins:
            return

        pluginclass = self.pyload.pgm.load_class('addon', plugin)

        if not pluginclass:
            return

        self.pyload.log.debug('Plugin loaded: {0}'.format(plugin))

        plugin = pluginclass(self.pyload, self)
        self.plugins[pluginclass.__name__].instances.append(plugin)

        # active the addon in new thread
        start_new_thread(plugin.activate, tuple())
        self.register_events()

    @lock
    def deactivate_addon(self, plugin):
        if plugin not in self.plugins:
            return
        else:  # TODO: multiple instances
            addon = self.plugins[plugin].instances[0]

        if addon.__internal__:
            return

        self.call(addon, 'deactivate')
        self.pyload.log.debug('Plugin deactivated: {0}'.format(plugin))

        # remove periodic call
        self.pyload.log.debug('Removed callback {0}'.format(
            self.pyload.scheduler.cancel(addon.cb)))

        # TODO: only delete instances, meta data is lost otherwise
        del self.plugins[addon.__name__].instances[:]

        # TODO: could be improved
        # remove event listener
        for fname in dir(addon):
            if fname.startswith('__') or not isinstance(
                    getattr(addon, fname), MethodType):
                continue
            self.pyload.evm.remove_from_events(getattr(addon, fname))

    def activate_addons(self):
        self.pyload.log.info(self._('Activating addons...'))
        for plugin in self.plugins.values():
            for inst in plugin.instances:
                if inst.is_activated():
                    self.call(inst, 'activate')

        self.register_events()

    def deactivate_addons(self):
        """Called when core is shutting down."""
        self.pyload.log.info(self._('Deactivating addons...'))
        for plugin in self.plugins.values():
            for inst in plugin.instances:
                self.call(inst, 'deactivate')

    def download_preparing(self, file):
        self.call_in_hooks('pre_download', 'download:preparing', file)

    def download_finished(self, file):
        self.call_in_hooks('download_finished', 'download:finished', file)

    def download_failed(self, file):
        self.call_in_hooks('download_failed', 'download:failed', file)

    def package_finished(self, package):
        self.call_in_hooks('package_finished', 'package:finished', package)

    @lock
    def start_thread(self, func, *args, **kwargs):
        thread = AddonThread(self.pyload.iom, func, args, kwargs)
        thread.start()
        return thread

    def active_plugins(self):
        """Returns all active plugins."""
        return [inst for plugin in self.plugins.values()
                for inst in plugin.instances if inst.is_activated()]

    def get_info(self, plugin):
        """Retrieves all info data for a plugin."""
        data = []
        # TODO
        if plugin in self.plugins:
            if plugin.instances:
                for attr in dir(plugin.instances[0]):
                    if attr.startswith('__Property'):
                        info = self.info_props[attr]
                        info.value = getattr(plugin.instances[0], attr)
                        data.append(info)
        return data

    def add_event_listener(self, plugin, func, event):
        """Add the event to the list."""
        self.plugins[plugin].events.append((func, event))

    def register_events(self):
        """Actually register all saved events."""
        for name, plugin in self.plugins.items():
            for func, event in plugin.events:
                for inst in plugin.instances:
                    self.listen_to(event, getattr(inst, func))

    def add_addon_handler(self, plugin, func, label,
                          desc, args, package, media):
        """Registers addon service description."""
        self.plugins[plugin].handler[func] = AddonService(
            func, gettext(label), gettext(desc), args, package, media)

    def add_info_property(self, h, name, desc):
        """Register property as :class:`AddonInfo`."""
        self.info_props[h] = AddonInfo(name, desc)

    def listen_to(self, *args):
        self.pyload.evm.listen_to(*args)

    def fire(self, *args):
        self.pyload.evm.fire(*args)
