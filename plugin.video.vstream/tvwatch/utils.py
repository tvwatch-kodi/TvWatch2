# -*- coding: utf-8 -*-

import base64
import requests
from urllib3.util import connection
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

                title_raw = title_raw.strip()
                title_raw = title_raw.lower()
                while "  " in title_raw:
                     title_raw = title_raw.replace("  ", " ")

                title_raw = title_raw.replace(pattern+" ", pattern)
                title_raw = title_raw.replace(pattern + str(number), "")
                title_raw = title_raw.replace(pattern + "0" + str(number), "")
                title_raw = title_raw.strip()
                if "-" == title_raw[0]:
                    title_raw = title_raw[1:].strip()

                title_raw = title_raw.split(' ')
                for i in range(len(title_raw)):
                    title_raw[i] = title_raw[i].capitalize()

                title_raw = ' '.join(title_raw)

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

def testUrl(url, time_out = 1, dns=False):
    code = 0
    try:
        res = requests.get(url, timeout = time_out)
        code = res.status_code
    except Exception, e:
        if 'getaddrinfo failed' in str(e.message) and dns == False:
            VSlog("testUrl: Retry with DNS resolver")
            return testUrlDNS(url, time_out)
        VSlog("ERROR testUrl:" + str(e.message))
    return (code == 200)

def testUrlDNS(url, time_out = 1):
    _orig_create_connection = connection.create_connection

    def patched_create_connection(address, *args, **kwargs):
        """Wrap urllib3's create_connection to resolve the name elsewhere"""
        # resolve hostname to an ip address; use your own
        # resolver here, as otherwise the system resolver will be used.
        host, port = address

        try:
            import dns.resolver
            # Keep the domain only: http://example.com/foo/bar => example.com
            if "//" in host:
                host = host[host.find("//"):]
            if "/" in host:
                host = host[:host.find("/")]
            resolver = dns.resolver.Resolver(configure=False)
            # Résolveurs DNS ouverts: https://www.fdn.fr/actions/dns/
            resolver.nameservers = ['80.67.169.12', '2001:910:800::12', '80.67.169.40', '2001:910:800::40']
            answer = resolver.query(host, 'a')
            hostname = str(answer[0])
            VSlog("patched_create_connection found host %s" % hostname)
        except Exception as e:
            VSlog("patched_create_connection ERROR: {0}".format(e))
            return _orig_create_connection(address, *args, **kwargs)

        return _orig_create_connection((hostname, port), *args, **kwargs)

    connection.create_connection = patched_create_connection

    status = testUrl(url, time_out, dns=True)

    connection.create_connection = _orig_create_connection

    return status
