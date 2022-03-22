# -*- coding: utf-8 -*-

from __future__ import with_statement

import os
import re
import traceback

from pyload.plugin.Addon import Addon, threaded
from pyload.utils import fs_join


class MergeFiles(Addon):
    __name    = "MergeFiles"
    __type    = "addon"
    __version = "0.14"

    __config = [("activated", "bool", "Activated", True)]

    __description = """Merges parts splitted with hjsplit"""
    __license     = "GPLv3"
    __authors     = [("and9000", "me@has-no-mail.com")]


    BUFFER_SIZE = 4096


    @threaded
    def packageFinished(self, pack):
        files = {}
        fid_dict = {}
        for fid, data in pack.getChildren().iteritems():
            if re.search("\.\d{3}$", data['name']):
                if data['name'][:-4] not in files:
                    files[data['name'][:-4]] = []
                files[data['name'][:-4]].append(data['name'])
                files[data['name'][:-4]].sort()
                fid_dict[data['name']] = fid

        download_folder = self.config.get("general", "download_folder")

        if self.config.get("general", "folder_per_package"):
            download_folder = fs_join(download_folder, pack.folder)

        for name, file_list in files.iteritems():
            self.logInfo(_("Starting merging of"), name)

            with open(fs_join(download_folder, name), "wb") as final_file:
                for splitted_file in file_list:
                    self.logDebug("Merging part", splitted_file)

                    pyfile = self.core.files.getFile(fid_dict[splitted_file])

                    pyfile.setStatus("processing")

                    try:
                        with open(fs_join(download_folder, splitted_file), "rb") as s_file:
                            size_written = 0
                            s_file_size = int(os.path.getsize(os.path.join(download_folder, splitted_file)))

                            while True:
                                f_buffer = s_file.read(self.BUFFER_SIZE)
                                if f_buffer:
                                    final_file.write(f_buffer)
                                    size_written += self.BUFFER_SIZE
                                    pyfile.setProgress((size_written * 100) / s_file_size)
                                else:
                                    break

                        self.logDebug("Finished merging part", splitted_file)

                    except Exception, e:
                        traceback.print_exc()

                    finally:
                        pyfile.setProgress(100)
                        pyfile.setStatus("finished")
                        pyfile.release()

            self.logInfo(_("Finished merging of"), name)
