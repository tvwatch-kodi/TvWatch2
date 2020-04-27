# -*- coding: utf-8 -*-
# https://github.com/Kodi-vStream/venom-xbmc-addons
#
import urllib
import urllib2
import socket

from urllib2 import HTTPError, URLError
from resources.lib.comaddon import addon, dialog, VSlog

prv_getaddrinfo = socket.getaddrinfo
def new_getaddrinfo(*args):
	dns_cache = {}
	try:
		import dns.resolver
		host = args[0]
		port = args[1]
		VSlog((host, port))
		a = 0
		if "//" in host:
			a = host.find("//")
		b = 0
		if "/" in host[a+2:]:
			b = host[a+2:].find("/") + a + 2
		if a != 0 or b != 0:
			host = host[a:b]
			VSlog((host, port))
		resolver = dns.resolver.Resolver(configure=False)
		resolver.nameservers = [ '80.67.169.12', '2001:910:800::12', '80.67.169.40', '2001:910:800::40' ]
		answer = resolver.query(host, 'a')
		host = str(answer[0])
		return [(2, 1, 0, '', (host, port)), (2, 1, 0, '', (host, port))]
	except Exception, e:
		VSlog("new_getaddrinfo ERROR: " + e.message)
		return prv_getaddrinfo(*args)

class cRequestHandler:
    REQUEST_TYPE_GET = 0
    REQUEST_TYPE_POST = 1
    DIALOG = dialog()
    ADDON = addon()

    def __init__(self, sUrl):
        self.__sUrl = sUrl
        self.__sRealUrl = ''
        self.__cType = 0
        self.__aParamaters = {}
        self.__aParamatersLine = ''
        self.__aHeaderEntries = []
        self.removeBreakLines(True)
        self.removeNewLines(True)
        self.__setDefaultHeader()
        self.__timeout = 30
        self.__bRemoveNewLines = False
        self.__bRemoveBreakLines = False
        self.__sResponseHeader = ''
        self.BUG_SSL = False
        self.__enableDNS = False

    def removeNewLines(self, bRemoveNewLines):
        self.__bRemoveNewLines = bRemoveNewLines

    def removeBreakLines(self, bRemoveBreakLines):
        self.__bRemoveBreakLines = bRemoveBreakLines

    def setRequestType(self, cType):
        self.__cType = cType

    def setTimeout(self, valeur):
        self.__timeout = valeur

    def addHeaderEntry(self, sHeaderKey, sHeaderValue):
        for sublist in self.__aHeaderEntries:
            if sHeaderKey in sublist:
                self.__aHeaderEntries.remove(sublist)
        aHeader = {sHeaderKey: sHeaderValue}
        self.__aHeaderEntries.append(aHeader)

    def addParameters(self, sParameterKey, mParameterValue):
        self.__aParamaters[sParameterKey] = mParameterValue

    def addParametersLine(self, mParameterValue):
        self.__aParamatersLine = mParameterValue

    #egg addMultipartFiled({'sess_id': sId, 'upload_type': 'url', 'srv_tmp_url': sTmp})
    def addMultipartFiled(self, fields):
        mpartdata = MPencode(fields)
        self.__aParamatersLine = mpartdata[1]
        self.addHeaderEntry('Content-Type', mpartdata[0] )
        self.addHeaderEntry('Content-Length', len(mpartdata[1]))

    # Je sais plus si elle gere les doublons
    def getResponseHeader(self):
        return self.__sResponseHeader

    # url after redirects
    def getRealUrl(self):
        return self.__sRealUrl

    def GetCookies(self):
        if not self.__sResponseHeader:
            return ''
        if 'Set-Cookie' in self.__sResponseHeader:
            import re

            #cookie_string = self.__sResponseHeader.getheaders('set-cookie')
            #c = ''
            #for i in cookie_string:
            #    c = c + i + ', '
            c = self.__sResponseHeader.get('set-cookie')

            c2 = re.findall('(?:^|,) *([^;,]+?)=([^;,\/]+?);', c)
            if c2:
                cookies = ''
                for cook in c2:
                    cookies = cookies + cook[0] + '=' + cook[1] + ';'
                cookies = cookies[:-1]
                return cookies
        return ''

    def request(self):
        # Supprimee car deconne si url contient ' ' et '+' en meme temps
        #self.__sUrl = self.__sUrl.replace(' ', '+')
        return self.__callRequest()

    def getRequestUri(self):
        return self.__sUrl + '?' + urllib.urlencode(self.__aParamaters)

    def __setDefaultHeader(self):
        self.addHeaderEntry('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0')
        self.addHeaderEntry('Accept-Language', 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3')
        self.addHeaderEntry('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7')

    def __callRequest(self):
        if self.__enableDNS:
            socket.getaddrinfo = new_getaddrinfo

        if self.__aParamatersLine:
            sParameters = self.__aParamatersLine
        else:
            sParameters = urllib.urlencode(self.__aParamaters)

        if (self.__cType == cRequestHandler.REQUEST_TYPE_GET):
            if (len(sParameters) > 0):
                if (self.__sUrl.find('?') == -1):
                    self.__sUrl = self.__sUrl + '?' + str(sParameters)
                    sParameters = ''
                else:
                    self.__sUrl = self.__sUrl + '&' + str(sParameters)
                    sParameters = ''

        if (len(sParameters) > 0):
            oRequest = urllib2.Request(self.__sUrl, sParameters)
        else:
            oRequest = urllib2.Request(self.__sUrl)

        for aHeader in self.__aHeaderEntries:
            for sHeaderKey, sHeaderValue in aHeader.items():
                oRequest.add_header(sHeaderKey, sHeaderValue)

        sContent = ''
        try:

            if self.BUG_SSL:
                VSlog('Retrying with SSL bug')
                import ssl
                gcontext = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
                oResponse = urllib2.urlopen(oRequest, timeout = self.__timeout, context=gcontext)
            else:
                oResponse = urllib2.urlopen(oRequest, timeout = self.__timeout)

            sContent = oResponse.read()

            self.__sResponseHeader = oResponse.info()

            # compressed page ?
            if self.__sResponseHeader.get('Content-Encoding') == 'gzip':
                import zlib
                sContent = zlib.decompress(sContent, zlib.MAX_WBITS|16)

            # https://bugs.python.org/issue4773
            self.__sRealUrl = oResponse.geturl()
            self.__sResponseHeader = oResponse.info()

            oResponse.close()

        except urllib2.HTTPError, e:
            if e.code == 503:

                # Protected by cloudFlare ?
                from resources.lib import cloudflare
                if cloudflare.CheckIfActive(e.read()):
                    self.__sResponseHeader = e.hdrs
                    cookies = self.GetCookies()
                    VSlog('Page protegee par cloudflare')
                    CF = cloudflare.CloudflareBypass()
                    sContent = CF.GetHtml(self.__sUrl, e.read(), cookies, sParameters, oRequest.headers)
                    self.__sRealUrl, self.__sResponseHeader = CF.GetReponseInfo()
                else:
                    sContent = e.read()
                    self.__sRealUrl = e.geturl()
                    self.__sResponseHeader = e.headers()

            else:
                try:
                    VSlog("%s (%d),%s" % (self.ADDON.VSlang(30205), e.code, self.__sUrl))
                    self.__sRealUrl = e.geturl()
                    self.__sResponseHeader = e.headers
                    sContent = e.read()
                except:
                    sContent = ''

            if not sContent:
                VSlog("%s 1: (%d),%s" % (VSlang(30205), e.code , self.__sUrl))
                if self.__enableDNS:
                    socket.getaddrinfo = prv_getaddrinfo
                    self.__enableDNS = False
                return ''

        except urllib2.URLError, e:
            VSlog("%s 2: (%s),%s" % (VSlang(30205), e.reason , self.__sUrl))
            if 'CERTIFICATE_VERIFY_FAILED' in str(e.reason) and self.BUG_SSL == False:
                self.BUG_SSL = True
                return self.__callRequest()
            # elif 'getaddrinfo failed' in str(e.reason) and self.__enableDNS == False:
            elif self.__enableDNS == False:
                self.__enableDNS = True
                return self.__callRequest()

        except Exception, e:
			VSlog("%s 3: (%s),%s" % (VSlang(30205), e.message , self.__sUrl))
			return ''

        if (self.__bRemoveNewLines == True):
            sContent = sContent.replace("\n", "")
            sContent = sContent.replace("\r\t", "")

        if (self.__bRemoveBreakLines == True):
            sContent = sContent.replace("&nbsp;", "")

        if self.__enableDNS:
            socket.getaddrinfo = prv_getaddrinfo
            self.__enableDNS = False

        return sContent

    def getHeaderLocationUrl(self):
        opened = urllib.urlopen(self.__sUrl)
        return opened.geturl()

# ******************************************************************************
# from https://github.com/eliellis/mpart.py
# ******************************************************************************


def MPencode(fields):
    import mimetypes
    random_boundary = __randy_boundary()
    content_type = "multipart/form-data, boundary=%s" % random_boundary

    form_data = []

    if fields:
        for (key, value) in fields.iteritems():
            if not hasattr(value, 'read'):
                itemstr = '--%s\r\nContent-Disposition: form-data; name="%s"\r\n\r\n%s\r\n' % (random_boundary, key, value)
                form_data.append(itemstr)
            elif hasattr(value, 'read'):
                with value:
                    file_mimetype = mimetypes.guess_type(value.name)[0] if mimetypes.guess_type(value.name)[0] else 'application/octet-stream'
                    itemstr = '--%s\r\nContent-Disposition: form-data; name="%s"; filename="%s"\r\nContent-Type: %s\r\n\r\n%s\r\n' % (random_boundary, key, value.name, file_mimetype, value.read())
                form_data.append(itemstr)
            else:
                raise Exception(value, 'Field is neither a file handle or any other decodable type.')
    else:
        pass

    form_data.append('--%s--\r\n' % random_boundary)

    return content_type, ''.join(form_data)


def __randy_boundary(length=10, reshuffle=False):
    import string
    import random

    character_string = string.letters + string.digits
    boundary_string = []
    for i in range(0, length):
        rand_index = random.randint(0, len(character_string) - 1)
        boundary_string.append(character_string[rand_index])
    if reshuffle:
        random.shuffle(boundary_string)
    else:
        pass
    return ''.join(boundary_string)
