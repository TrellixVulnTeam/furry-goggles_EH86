# -*- coding: utf-8 -*-

import os
import re
import time

from ..captcha.ReCaptcha import ReCaptcha
from ..internal.misc import json
from ..internal.SimpleHoster import SimpleHoster


class UploadedTo(SimpleHoster):
    __name__ = "UploadedTo"
    __type__ = "hoster"
    __version__ = "1.11"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.)?(uploaded\.(to|net)|ul\.to)(/file/|/?\?id=|.*?&id=|/)(?P<ID>\w+)'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("fallback", "bool", "Fallback to free download if premium fails", True),
                  ("chk_filesize", "bool", "Check file size", True),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Uploaded.net hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com"),
                   ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    CHECK_TRAFFIC = True

    URL_REPLACEMENTS = [(__pattern__ + ".*", r'http://uploaded.net/file/\g<ID>')]

    API_KEY = "lhF2IeeprweDfu9ccWlxXVVypA5nA3EL"

    OFFLINE_PATTERN = r'>Page not found'
    TEMP_OFFLINE_PATTERN = r'<title>uploaded\.net - Maintenance|Downloads have been blocked for today.<'
    PREMIUM_ONLY_PATTERN = r'This file exceeds the max\. filesize which can be downloaded by free users'

    LINK_FREE_PATTERN = r"url:\s*'(.+?)'"
    LINK_PREMIUM_PATTERN = r'<div class="tfree".*\s*<form method="post" action="(.+?)"'

    WAIT_PATTERN = r'(?:Current waiting period|Aktuelle Wartezeit): <span>(\d+)'
    DL_LIMIT_PATTERN = r'You have reached the max. number of possible free downloads for this hour'

    def api_info(self, url):
        info = {}

        for _i in range(5):
            html = self.load("http://uploaded.net/api/filemultiple",
                             get={'apikey': self.API_KEY,
                                  'id_0': re.match(self.__pattern__, url).group('ID')},
                             decode=False)

            if html != "can't find request":
                api = html.split(",", 4)
                if api[0] == "online":
                    info.update({
                        'size': api[2],
                        'status': 2,
                        'sha1': api[3]
                    })
                    name = api[4].strip()
                    try:
                        info['name'] = name.decode('latin1')
                    except (UnicodeDecodeError, UnicodeEncodeError):
                        info['name'] = name.decode('utf8')
                    except (UnicodeDecodeError, UnicodeEncodeError):
                        info['name'] = name

                else:
                    info['status'] = 1
                break
            else:
                time.sleep(3)

        return info

    def setup(self):
        self.multiDL = self.resume_download = self.premium
        self.chunk_limit = 1  #: Critical problems with more chunks

    def handle_free(self, pyfile):
        self.load("http://uploaded.net/language/en", just_header=True)

        self.data = self.load("http://uploaded.net/js/download.js")

        self.captcha = ReCaptcha(pyfile)
        response = self.captcha.challenge()

        self.data = self.load("http://uploaded.net/io/ticket/captcha/%s" % self.info['pattern']['ID'],
                              post={'g-recaptcha-response': response})
        self.check_errors()

        try:
            json_data = json.loads(self.data)
            if 'err' in json_data:
                if json_data['err'] == "captcha":
                    self.retry_captcha()

                else:
                    self.error(_("Unknown error `%s`" % json_data['err']))

        except ValueError:
            pass

        m = re.search(self.LINK_FREE_PATTERN, self.data)
        if m is not None:
            self.captcha.correct()
            self.link = m.group(1)