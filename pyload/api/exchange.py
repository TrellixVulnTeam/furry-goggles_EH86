# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from future import standard_library

from pyload.api.base import BaseApi, requireperm
from pyload.core.datatype.base import Permission
from pyload.core.datatype.task import Interaction

standard_library.install_aliases()


class UserExchangeApi(BaseApi):
    """Everything needed for user interaction."""
    @requireperm(Permission.Interaction)
    def is_interaction_waiting(self, mode):
        """Check if task is waiting.

        :param mode: binary or'ed output type
        :return: boolean

        """
        return self.pyload.im.is_task_waiting(mode)

    @requireperm(Permission.Interaction)
    def get_interaction_tasks(self, mode):
        """Retrieve task for specific mode.

        :param mode: binary or'ed interaction types which should be retrieved
        :rtype list of :class:`InteractionTask`

        """
        tasks = self.pyload.im.get_tasks(mode)
        # retrieved tasks count as seen
        for tsk in tasks:
            tsk.seen = True
            if tsk.type == Interaction.Notification:
                tsk.set_waiting(self.pyload.im.CLIENT_THRESHOLD)

        return tasks

    @requireperm(Permission.Interaction)
    def set_interaction_result(self, iid, result):
        """Set Result for a interaction task. It will be immediately removed
        from task queue afterwards.

        :param iid: interaction id
        :param result: result as json string

        """
        task = self.pyload.im.get_task_by_id(iid)
        if task:
            task.set_result(result)

    @requireperm(Permission.Interaction)
    def get_addon_handler(self):
        raise NotImplementedError

    @requireperm(Permission.Interaction)
    def call_addon_handler(self, plugin, func, pid_or_fid):
        raise NotImplementedError

    @requireperm(Permission.Download)
    def generate_download_link(self, fid, timeout):
        raise NotImplementedError
