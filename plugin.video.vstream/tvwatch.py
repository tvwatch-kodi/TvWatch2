#-*- coding: utf-8 -*-

from resources.lib.home import cHome
from resources.sites import freebox
from resources.lib.gui.gui import cGui
from resources.lib.handler.inputParameterHandler import cInputParameterHandler
from resources.lib.handler.outputParameterHandler import cOutputParameterHandler
from resources.lib.util import Quote
from resources.lib.comaddon import addon, VSlog, dialog

addons = addon()

class cPatches:
    addons = addons
    def __init__(self):
        exec _("c2VsZi51c2VyTiwgc2VsZi5wYXNzVyA9ICJ6YWthcmlhMjIwJGNvZGU3NDYxKyIuc3BsaXQoIiQiKQ==")
        self.server_name = 'zt_stream'
        self.server_process_function = 'showMovies'
        self.server_main_url = 'https://www.zone-telechargement.stream/'
        self.server_search = (self.server_main_url + 'engine/ajax/controller.php?mod=filter&q=', 'showSearch')
        self.server_search_movies = (self.server_main_url + 'engine/ajax/controller.php?mod=filter&catid=0&categorie%5B%5D=2&q=', 'showSearch')
        self.server_search_series = (self.server_main_url + 'engine/ajax/controller.php?mod=filter&catid=0&categorie%5B%5D=15&q=', 'showSearch')


    def server_load(self):
        oGui = cGui()

        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', self.server_search[0])
        oGui.addDir(self.server_name, self.server_search[1], addons.VSlang(30076), 'search.png', oOutputParameterHandler)

        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', 'http://venom')
        oGui.addDir('themoviedb_org', 'load', 'TheMovieDB Search', 'searchtmdb.png', oOutputParameterHandler)

        if (addons.getSetting('history-view') == 'true'):
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

        view = False
        if (addons.getSetting('active-view') == 'true'):
            view = addons.getSetting('accueil-view')

        oGui.setEndOfDirectory(view)

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
        cGui.createContexMenuWatch = self.createContexMenuWatch

        # Patch method CreateSimpleMenu of cGui
        save_CreateSimpleMenu = cGui.CreateSimpleMenu
        def new_CreateSimpleMenu(self, oGuiElement, oOutputParameterHandler, sFile, sName, sFunction, sTitle):
            if sFunction != 'UptomyAccount' and sFunction != 'setLibrary':
                return save_CreateSimpleMenu(self, oGuiElement, oOutputParameterHandler, sFile, sName, sFunction, sTitle)
        cGui.CreateSimpleMenu = new_CreateSimpleMenu

        # Patch method VSinfo of dialog
        save_VSinfo = dialog.VSinfo
        def new_VSinfo(self, desc, title = 'vStream', iseconds = 0, sound = False):
            if title.lower() == 'vstream':
                return save_VSinfo(self, desc, 'TvWatch', iseconds, sound)
            if title.lower() != 'resolve' and title.lower() != 'premium mode':
                return save_VSinfo(self, desc, title, iseconds, sound)
        dialog.VSinfo = new_VSinfo

        # Patch method VSsetting of addon
        save_VSsetting = addon.VSsetting
        def new_VSsetting(self, name, value = False):
            if name == 'hoster_uptobox_premium':
                return "true"
            elif name == 'hoster_uptobox_username':
                return self.userN
            elif name == 'hoster_uptobox_password':
                return self.passW
            else:
                return save_VSsetting(self, name, value)
        addon.VSsetting = new_VSsetting

    def createContexMenuWatch(self, oGuiElement, oOutputParameterHandler= ''):
        return

    def searchGlobal(self):
        oGui = cGui()
        oInputParameterHandler = cInputParameterHandler()
        sSearchText = oInputParameterHandler.getValue('searchtext')
        # sCat = oInputParameterHandler.getValue('sCat')
        # if sCat == "1":
        #     sUrl = self.server_search_movies[0]
        # else:
        #     sUrl = self.server_search_series[1]

        sUrl = self.server_search[0]
        sUrl = sUrl + Quote(sSearchText)

        plugins = __import__('resources.sites.%s' % self.server_name, fromlist = [self.server_name])
        function = getattr(plugins, self.server_process_function)
        function(sUrl)

        oGui.setEndOfDirectory()
