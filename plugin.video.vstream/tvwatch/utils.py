# -*- coding: utf-8 -*-

import base64
import requests
from resources.lib.comaddon import VSlog

def str_conv(data):
    data = data.strip()
    data = base64.b16encode(data)
    return data

def str_deconv(data):
    data = base64.b16decode(data)
    data = data.strip()
    return data

def get_season_episode(title):
    title_raw = title
    saison_int = 0
    episode_int = 0

    def find_next_int(title_raw, title, pattern):
        number = 0
        try:
            if pattern in title.lower():
                title_raw = title_raw[:title_raw.lower().rfind(pattern)]
                if title_raw.replace(" ", "") == "":
                    title_raw = title
                string_se = title[title.lower().rfind(pattern)+len(pattern):]
                str_unicode = u''
                for char in string_se:
                    if not isinstance(char, unicode):
                        char = unicode(char, 'utf-8')
                    if char.isnumeric():
                        str_unicode += char
                    elif str_unicode != u'':
                        break
                if str_unicode != u'':
                    number = int(str_unicode)
        except Exception as err:
            VSlog("Exception get_season_episode: {0}".format(err))
            VSlog('ERROR get_season_episode title: ' + title)
        return number, title_raw

    saison_int, title_raw = find_next_int(title_raw, title, 'saison')
    if saison_int == 0: saison_int, title_raw = find_next_int(title_raw, title, 'season')
    if saison_int == 0: saison_int, title_raw = find_next_int(title_raw, title, 's')

    episode_int, title_raw = find_next_int(title_raw, title, 'episode')
    if episode_int == 0: episode_int, title_raw = find_next_int(title_raw, title, 'ep')
    if episode_int == 0: episode_int, title_raw = find_next_int(title_raw, title, 'e')

    VSlog(title + ": s(%s) e(%s) raw(%s)" % (saison_int, episode_int, title_raw))
    return saison_int, episode_int, title_raw

def testUrl(url, time_out = 1):
    code = 0
    try:
        res = requests.get(url, timeout = time_out)
        code = res.status_code
    except Exception, e:
        VSlog("ERROR " + str(e.message))
    return (code == 200)
