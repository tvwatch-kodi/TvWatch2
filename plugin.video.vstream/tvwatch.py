#-*- coding: utf-8 -*-

import requests
from resources.lib.home import cHome
from resources.sites import freebox
from resources.lib.gui.gui import cGui
from resources.lib.player import cPlayer
from resources.lib.gui.hoster import cHosterGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.inputParameterHandler import cInputParameterHandler
from resources.lib.handler.outputParameterHandler import cOutputParameterHandler
from resources.lib.util import Quote, UnquotePlus, QuotePlus
from resources.lib.db import cDb
from resources.lib.comaddon import addon, VSlog, dialog, progress, VSupdate
from resources.hosters import uptostream
from resources.hosters import uptobox

addons = addon()

CURRENT_SERVER = 'zt_stream'
CURRENT_SEARCH_FUNCTION_NAME = 'showSearch'

class cPatches:
    addons = addons
    def __init__(self):
        self.server_name = CURRENT_SERVER
        self.server_search_function_name = CURRENT_SEARCH_FUNCTION_NAME

        plugins = __import__('resources.sites.%s' % self.server_name, fromlist = [self.server_name])
        setattr(plugins, "SITE_NAME", '[COLOR violet]TvWatch2[/COLOR]')
        self.server_main_url = getattr(plugins, 'URL_MAIN')
        self.server_search = getattr(plugins, 'URL_SEARCH')
        self.server_search_movies = getattr(plugins, 'URL_SEARCH_MOVIES')
        self.server_search_series = getattr(plugins, 'URL_SEARCH_SERIES')
        self.server_process_function_name = getattr(plugins, 'FUNCTION_SEARCH')
        self.server_process_function = getattr(plugins, self.server_process_function_name)

    def server_load(self):
        oGui = cGui()

        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', self.server_search[0])
        oGui.addDir(self.server_name, self.server_search_function_name, addons.VSlang(30076), 'search.png', oOutputParameterHandler)

        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', 'http://venom')
        oGui.addDir('themoviedb_org', 'load', 'TheMovieDB Search', 'searchtmdb.png', oOutputParameterHandler)

        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', 'http://venom')
        oGui.addDir('cHome', 'showHistory', '[B][COLOR khaki]' + addons.VSlang(30470) + '[/COLOR][/B]', 'annees.png', oOutputParameterHandler)

        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', 'http://venom')
        oGui.addDir(self.server_name, 'showMenuFilms', addons.VSlang(30120), 'films.png', oOutputParameterHandler)

        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', 'http://venom')
        oGui.addDir(self.server_name, 'showMenuSeries', addons.VSlang(30121), 'series.png', oOutputParameterHandler)

        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', 'http://venom')
        oGui.addDir(self.server_name, 'showMenuMangas', addons.VSlang(30122), 'animes.png', oOutputParameterHandler)

        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', 'http://venom')
        oGui.addDir(self.server_name, 'showMenuAutres', addons.VSlang(30471), 'doc.png', oOutputParameterHandler)

        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', 'http://venom')
        oGui.addDir('freebox', 'load', addons.VSlang(30115), 'tv.png', oOutputParameterHandler)

        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', 'http://venom')
        oGui.addDir('cDownload', 'getDownload', addons.VSlang(30202), 'download.png', oOutputParameterHandler)

        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', 'http://venom')
        oGui.addDir('cFav', 'getBookmarks', addons.VSlang(30207), 'mark.png', oOutputParameterHandler)

        oGui.setEndOfDirectory(50)

    def showHistory(self):
        oGui = cGui()
        oDb = cDb()

        # Fetch all data from resume table
        matchedrow = []
        try:
            # oDb.dbcur.execute("DELETE FROM resume")
            # oDb.db.commit()
            sql_select = "SELECT * FROM resume"
            oDb.dbcur.execute(sql_select)
            matchedrow = oDb.dbcur.fetchall()
            if not matchedrow:
                matchedrow = []
        except Exception, e:
            VSlog('SQL ERROR GET resume: ' + str(e.message))
        ##################################

        progress_ = progress().VScreate("TvWatch2")
        matchedrow.reverse()
        for aEntry in matchedrow:
            sMovieTitle = UnquotePlus(aEntry[2])
            sItemUrl, sThumbnail, sDisplayTitle = UnquotePlus(aEntry[3]).split("&tvwatch&")

            progress_.VSupdate(progress_, len(matchedrow))
            if progress_.iscanceled():
                break

            oOutputParameterHandler = cOutputParameterHandler()
            oOutputParameterHandler.addParameter('sDisplayTitle', sDisplayTitle)
            oOutputParameterHandler.addParameter('sMovieTitle', sMovieTitle)
            oOutputParameterHandler.addParameter('sItemUrl', sItemUrl)
            oOutputParameterHandler.addParameter('searchtext', sMovieTitle)
            oOutputParameterHandler.addParameter('sThumbnail', sThumbnail)

            oGuiElement = cGuiElement()
            oGuiElement.setSiteName('globalSearch')
            oGuiElement.setFunction('globalSearch')
            oGuiElement.setTitle(sMovieTitle)
            oGuiElement.setThumbnail(sThumbnail)
            oGuiElement.setPoster(sThumbnail)
            oGuiElement.setMeta(2)
            oGuiElement.setCat(2)

            if "saison" in sDisplayTitle.lower() and "episode" in sDisplayTitle.lower():
                oOutputParameterHandler.addParameter('sCat', '2')
                cGui.CONTENT = 'tvshows'
                oGuiElement.setMeta(2)
                oGuiElement.setCat(2)
                # oGui.addTV('globalSearch', 'globalSearch', sMovieTitle, '', sThumbnail, '', oOutputParameterHandler)
            else:
                oOutputParameterHandler.addParameter('sCat', '1')
                cGui.CONTENT = 'movies'
                oGuiElement.setMeta(1)
                oGuiElement.setCat(1)
                # oGui.addMovie('globalSearch', 'globalSearch', sMovieTitle, '', sThumbnail, '', oOutputParameterHandler)

            # oGui.addDir('cHome', 'manageContinueWatching', sMovieTitle, sThumbnail, oOutputParameterHandler)
            oGui.CreateSimpleMenu(oGuiElement, oOutputParameterHandler, 'cHome', 'cHome', 'deleteFromHistory', addons.VSlang(30413))
            oGui.addFolder(oGuiElement, oOutputParameterHandler)

        progress_.VSclose(progress_)
        if len(matchedrow) == 0:
            oGui.addText("Tvwatch2",'[COLOR khaki]' + addons.VSlang(30472) + '[/COLOR]')
            oGui.setEndOfDirectory(50)
        else:
            oGui.setEndOfDirectory(500)

    def tv_radio_load(self):
        oGui = cGui()

        URL_WEB = 'https://raw.githubusercontent.com/Kodi-vStream/venom-xbmc-addons/Beta/repo/resources/webtv2.m3u'
        URL_RADIO = 'https://raw.githubusercontent.com/Kodi-vStream/venom-xbmc-addons/master/repo/resources/radio.m3u'

        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', URL_WEB)
        oGui.addDir('freebox', 'showWeb', addons.VSlang(30332), 'tv.png', oOutputParameterHandler)

        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', URL_RADIO)
        oGui.addDir('radio', 'showWeb', addons.VSlang(30203), 'music.png', oOutputParameterHandler)

        oGui.setEndOfDirectory()

    def applyPatches(self):
        cHome.load = self.server_load
        freebox.load = self.tv_radio_load
        cHome.showHistory = self.showHistory
        # cHome.showHostDirect = self.showHostDirect
        # cHome.manageContinueWatching = self.manageContinueWatching
        cHome.deleteFromHistory = self.deleteFromHistory
        cGui.createContexMenuWatch = self.createContexMenuWatch

        # Patch method showHoster of cHosterGui
        save_showHoster = cHosterGui.showHoster
        def new_showHoster(hos, oGui, oHoster, sMediaUrl, sThumbnail, bGetRedirectUrl = False):
            sDisplayName = oHoster.getDisplayName()
            sMovieTitle = oHoster.getFileName()

            sDisplayName = self.removeHoster(sDisplayName)
            sMovieTitle = self.removeHoster(sMovieTitle)

            if "episode" in sDisplayName.lower() and "saison" in sMovieTitle.lower():
                sDisplayName = sMovieTitle + " " + sDisplayName
                if "saison" in sMovieTitle.lower():
                    a = sMovieTitle.lower().find("saison")
                    sMovieTitle = sMovieTitle[:a]

            oHoster.__dict__['_cHoster__sDisplayName'] = sDisplayName.strip()
            oHoster.__dict__['_cHoster__sFileName'] = sMovieTitle.strip()

            return save_showHoster(hos, oGui, oHoster, sMediaUrl, sThumbnail, bGetRedirectUrl)
        cHosterGui.showHoster = new_showHoster

        # Patch method CreateSimpleMenu of cGui
        save_CreateSimpleMenu = cGui.CreateSimpleMenu
        def new_CreateSimpleMenu(gui, oGuiElement, oOutputParameterHandler, sFile, sName, sFunction, sTitle):
            if sFunction != 'UptomyAccount' and sFunction != 'setLibrary':
                return save_CreateSimpleMenu(gui, oGuiElement, oOutputParameterHandler, sFile, sName, sFunction, sTitle)
        cGui.CreateSimpleMenu = new_CreateSimpleMenu

        # Patch method VSinfo of dialog
        save_VSinfo = dialog.VSinfo
        def new_VSinfo(dia, desc, title = 'vStream', iseconds = 0, sound = False):
            if title.lower() == 'vstream':
                return save_VSinfo(dia, desc, 'TvWatch2', iseconds, sound)
            if title.lower() != 'resolve' and title.lower() != 'premium mode':
                return save_VSinfo(dia, desc, title, iseconds, sound)
        dialog.VSinfo = new_VSinfo

        # Patch method getMediaLink of uptostream and uptobox
        def getMediaLinkByUserToken(upto):
            FILE_CODE = upto.getUrl()
            if "/" in FILE_CODE:
                FILE_CODE = FILE_CODE.split("/")[-1]
            USR_TOKEN = "e84e2bdf19d127b4e624eed2c83bfd871tgrq"
            URL = "https://uptobox.com/api/link"
            PARAMS = {'token':USR_TOKEN, 'file_code':FILE_CODE}
            try:
                r = requests.get(url = URL, params = PARAMS)
                data = r.json()
                result = True, data['data']['dlLink']
            except Exception as err:
                VSlog("Exception getMediaLinkByUserToken: {0}".format(err))
                result = False, False
            return result
        uptostream.cHoster.getMediaLink = getMediaLinkByUserToken
        uptobox.cHoster.getMediaLink = getMediaLinkByUserToken

        # Patch method run of cPlayer
        save_run = cPlayer.run
        def new_run(player, oGuiElement, sTitle, sUrl):
            try:
                oDb = cDb()
                res = save_run(player, oGuiElement, sTitle, sUrl)

                meta = {}
                meta['site'] = sTitle
                meta['title'] = 'title'
                meta['point'] = QuotePlus(str(player.sSite) + "&tvwatch&" + str(player.sThumbnail) + "&tvwatch&" + player.sTitle)

                if oDb.get_resume(meta):
                    oDb.del_resume(meta)
                oDb.insert_resume(meta)

            except Exception as err:
                VSlog("Exception new_run: {0}".format(err))
            return res
        cPlayer.run = new_run

    def createContexMenuWatch(self, oGuiElement, oOutputParameterHandler= ''):
        return

    def searchGlobal(self):
        oGui = cGui()
        oInputParameterHandler = cInputParameterHandler()
        sSearchText = oInputParameterHandler.getValue('searchtext')
        sCat = oInputParameterHandler.getValue('sCat')
        if sCat == "1":
            sUrl = self.server_search_movies[0]
        elif sCat == "2":
            sUrl = self.server_search_series[0]
        else:
            sUrl = self.server_search[0]

        sUrl = sUrl + Quote(sSearchText)
        self.server_process_function(sUrl)
        oGui.setEndOfDirectory(50)

    def deleteFromHistory(self):
        oInputParameterHandler = cInputParameterHandler()
        sMovieTitle = oInputParameterHandler.getValue('sMovieTitle')

        meta = {}
        meta['site'] = sMovieTitle

        cDb().del_resume(meta)

        VSupdate()

    def manageContinueWatching(self):
        oGui = cGui()

        oInputParameterHandler = cInputParameterHandler()
        sDisplayTitle = oInputParameterHandler.getValue('sDisplayTitle')
        sMovieTitle = oInputParameterHandler.getValue('sMovieTitle')
        sItemUrl = oInputParameterHandler.getValue('sItemUrl')
        sCat = oInputParameterHandler.getValue('sCat')
        sThumbnail = oInputParameterHandler.getValue('sThumbnail')

        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('sDisplayTitle', sDisplayTitle)
        oOutputParameterHandler.addParameter('sMovieTitle', sMovieTitle)
        oOutputParameterHandler.addParameter('sItemUrl', sItemUrl)

        if sCat == "1":
            oGui.addTV('cHome', 'showHostDirect', sMovieTitle, '', sThumbnail, '', oOutputParameterHandler)
        elif sCat == "2":
            oGui.addMovie('cHome', 'showHostDirect', sMovieTitle, '', sThumbnail, '', oOutputParameterHandler)

        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('searchtext', sMovieTitle)
        oOutputParameterHandler.addParameter('sCat', sCat)
        oGui.addDir('globalSearch', 'globalSearch', 'Search', 'search.png', oOutputParameterHandler)

        oGui.setEndOfDirectory(50)

    def showHostDirect(self):
        oGui = cGui()
        oInputParameterHandler = cInputParameterHandler()
        sDisplayTitle = oInputParameterHandler.getValue('sDisplayTitle')
        sMovieTitle = oInputParameterHandler.getValue('sMovieTitle')
        sItemUrl = oInputParameterHandler.getValue('sItemUrl')
        # sThumbnail = oInputParameterHandler.getValue('sThumbnail')

        oHoster = cHosterGui().checkHoster(sItemUrl)
        if (oHoster != False):
            oHoster.setDisplayName(sDisplayTitle)
            oHoster.setFileName(sMovieTitle)
            cHosterGui().showHoster(oGui, oHoster, sItemUrl, '')
        oGui.setEndOfDirectory(50)

    def removeHoster(self, title):
        if "uptostream" in title.lower() or "uptobox" in title.lower():
            a = title.rfind("[COLOR ")
            title = title[:a]
        return title
