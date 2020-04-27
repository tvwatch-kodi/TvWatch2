#-*- coding: utf-8 -*-

import xbmcgui
import sys
import socket
import requests
import xbmc
from tvwatch.utils import str_conv, str_deconv, get_season_episode, testUrl
from upnext.utils import set_property
from upnext.statichelper import to_unicode, from_unicode
from resources.lib.home import cHome
from resources.sites import freebox
from resources.lib.gui.gui import cGui
from resources.lib.player import cPlayer
from resources.lib.gui.hoster import cHosterGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.inputParameterHandler import cInputParameterHandler
from resources.lib.handler.outputParameterHandler import cOutputParameterHandler
from resources.lib.handler.rechercheHandler import cRechercheHandler
from resources.lib.util import Unquote, Quote, UnquotePlus, QuotePlus
from resources.lib.db import cDb
from resources.lib.comaddon import addon, VSlog, dialog, progress, VSupdate
from resources.hosters import uptostream
from resources.hosters import uptobox

addons = addon()

DEFAULT_SERVER = 'zt_stream'
CURRENT_SEARCH_FUNCTION_NAME = 'showSearch'

class cPatches:
    addons = addons
    def __init__(self):
        self.server_name = self.chooseServer()
        self.server_search_function_name = CURRENT_SEARCH_FUNCTION_NAME

        self.plugin = __import__('resources.sites.%s' % self.server_name, fromlist = [self.server_name])
        self.server_main_url = getattr(self.plugin, 'URL_MAIN', None)
        self.server_search = getattr(self.plugin, 'URL_SEARCH', None)
        self.server_search_movies = getattr(self.plugin, 'URL_SEARCH_MOVIES', None)
        self.server_search_series = getattr(self.plugin, 'URL_SEARCH_SERIES', None)
        self.server_process_function_name = getattr(self.plugin, 'FUNCTION_SEARCH', None)
        if self.server_process_function_name:
            self.server_process_function = getattr(self.plugin, self.server_process_function_name, None)

        addons.setSetting('playerPlay', '0') # Use Play Method
        addons.setSetting('visuel-view', '500') # Use Play Method
        exec (str_deconv('6164646F6E732E73657453657474696E672827686F737465725F7570746F626F785F7072656D69756D272C2027747275652729'))
        exec (str_deconv('6164646F6E732E73657453657474696E672827686F737465725F7570746F626F785F757365726E616D65272C20277A616B617269613232302729'))
        exec (str_deconv('6164646F6E732E73657453657474696E672827686F737465725F7570746F626F785F70617373776F7264272C2027636F6465373436312B2729'))

    def getServers(self, foo):
        return [
                'zt_stream',
                # 'zone_streaming',
                'zone_telechargement_ws',
                'zustream',
                'free_telechargement_org',
                'filmstreamvk_com',
                'ddl1',
                'k_streaming',
                'libertyland_tv',
                'tirexo',
                'voirfilms_org'
                # 'extreme_down'
                ]

    def chooseServer(self):
        server_id = int(addons.getSetting('currentServer'))
        servers = self.getServers(None)
        if server_id >= 0 and server_id < len(servers):
            server_name = servers[server_id]
        else:
            server_name = DEFAULT_SERVER
        return server_name

    def server_load(self):
        oGui = cGui()

        # Search on all servers
        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', self.server_search[0])
        oGui.addDir('cHome', 'showSearchText', addons.VSlang(29968), 'search.png', oOutputParameterHandler)

        # Search on current server
        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', self.server_search[0])
        oGui.addDir(self.server_name, self.server_search_function_name, addons.VSlang(29969), 'search.png', oOutputParameterHandler)

        # visual search
        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', 'http://venom')
        oGui.addDir('themoviedb_org', 'load', addons.VSlang(30088), 'searchtmdb.png', oOutputParameterHandler)

        # continue watching
        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', 'http://venom')
        oGui.addDir('cHome', 'showHistory', '[B][COLOR khaki]' + addons.VSlang(29997) + '[/COLOR][/B]', 'annees.png', oOutputParameterHandler)

        # Movies
        if getattr(self.plugin, 'showMenuFilms', None) != None:
            oOutputParameterHandler = cOutputParameterHandler()
            oOutputParameterHandler.addParameter('siteUrl', 'http://venom')
            oGui.addDir(self.server_name, 'showMenuFilms', addons.VSlang(30120), 'films.png', oOutputParameterHandler)
        elif getattr(self.plugin, 'showMenuMovies', None) != None:
            oOutputParameterHandler = cOutputParameterHandler()
            oOutputParameterHandler.addParameter('siteUrl', 'http://venom')
            oGui.addDir(self.server_name, 'showMenuMovies', addons.VSlang(30120), 'films.png', oOutputParameterHandler)

        # Series
        if getattr(self.plugin, 'showMenuSeries', None) != None:
            oOutputParameterHandler = cOutputParameterHandler()
            oOutputParameterHandler.addParameter('siteUrl', 'http://venom')
            oGui.addDir(self.server_name, 'showMenuSeries', addons.VSlang(30121), 'series.png', oOutputParameterHandler)

        # Animes
        if getattr(self.plugin, 'showMenuMangas', None) != None:
            oOutputParameterHandler = cOutputParameterHandler()
            oOutputParameterHandler.addParameter('siteUrl', 'http://venom')
            oGui.addDir(self.server_name, 'showMenuMangas', addons.VSlang(30122), 'animes.png', oOutputParameterHandler)

        # Other items
        if getattr(self.plugin, 'showMenuAutres', None) != None:
            oOutputParameterHandler = cOutputParameterHandler()
            oOutputParameterHandler.addParameter('siteUrl', 'http://venom')
            oGui.addDir(self.server_name, 'showMenuAutres', addons.VSlang(29998), 'doc.png', oOutputParameterHandler)

        # My items
        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', 'http://venom/')
        oGui.addDir('siteuptobox', 'showFile', addons.VSlang(29996), 'genres.png', oOutputParameterHandler)

        # Television / Radio
        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', 'http://venom')
        oGui.addDir('freebox', 'load', addons.VSlang(30115), 'tv.png', oOutputParameterHandler)

        # Download
        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', 'http://venom')
        oGui.addDir('cDownload', 'getDownload', addons.VSlang(30202), 'download.png', oOutputParameterHandler)

        # Bookmarks
        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', 'http://venom')
        oGui.addDir('cFav', 'getBookmarks', addons.VSlang(30207), 'mark.png', oOutputParameterHandler)

        oGui.setEndOfDirectory(50)

        if addons.getSetting('do_not_show_hint_servers') != "true":
            text = "En cas de problème vous pouvez changer de serveur dans les paramètres de l'addon.\n\n"
            text += "Ne plus afficher ce message ?"
            result = dialog().VSyesno(text, "Astuce")
            if result == 1:
                addons.setSetting('do_not_show_hint_servers', 'true')

        if not testUrl(self.server_main_url, 5):
            text = "Ce serveur est indisponible pour le moment !"
            xbmcgui.Dialog().notification(self.server_name, text, xbmcgui.NOTIFICATION_ERROR, 10000)
            VSlog('Erreur: ' + str(text))

        server_id = int(addons.getSetting('currentServer'))
        servers = self.getServers(None)
        if server_id >= 0 and server_id < len(servers):
            for id in range(server_id):
                name = servers[id]
                plugin = __import__('resources.sites.%s' % name, fromlist = [name])
                server_main_url = getattr(plugin, 'URL_MAIN', None)
                if testUrl(server_main_url, 5):
                    text = "Un meilleur serveur [%s] est disponible !" % (name,)
                    xbmcgui.Dialog().notification("TvWatch2", text, xbmcgui.NOTIFICATION_INFO, 10000, False)
                    VSlog('Info: ' + str(text))
                    break

    def showHistory(self):
        oGui = cGui()

        # Fetch all data from myResume table
        matchedrow = self.get_resume()

        progress_ = progress().VScreate("TvWatch2")
        matchedrow.reverse()
        for aEntry in matchedrow:
            sMovieTitle = str_deconv(aEntry[1])
            sDisplayTitle = str_deconv(aEntry[2])
            sMediaUrl = UnquotePlus(aEntry[3])
            sThumbnail = UnquotePlus(aEntry[4])
            sHosterIdentifier = sMediaUrl[sMediaUrl.find('//')+len('//'):].split(".")[0]

            progress_.VSupdate(progress_, len(matchedrow))
            if progress_.iscanceled():
                break

            oOutputParameterHandler = cOutputParameterHandler()

            oOutputParameterHandler.addParameter('sDisplayTitle', sDisplayTitle)
            oOutputParameterHandler.addParameter('sMovieTitle', sMovieTitle)
            oOutputParameterHandler.addParameter('sMediaUrl', sMediaUrl)
            oOutputParameterHandler.addParameter('searchtext', sMovieTitle)
            oOutputParameterHandler.addParameter('sThumbnail', sThumbnail)
            oOutputParameterHandler.addParameter('sHosterIdentifier', sHosterIdentifier)
            oOutputParameterHandler.addParameter('sFileName', sDisplayTitle)
            oOutputParameterHandler.addParameter('sTitle', sDisplayTitle)
            oOutputParameterHandler.addParameter('siteUrl', sMediaUrl)
            oOutputParameterHandler.addParameter('previousFunction', 'showHistory')

            oGuiElement = cGuiElement()
            oGuiElement.setSiteName('globalSearch')
            oGuiElement.setFunction('globalSearch')
            oGuiElement.setTitle(sMovieTitle)
            oGuiElement.setThumbnail(sThumbnail)
            oGuiElement.setPoster(sThumbnail)

            s, e, t = get_season_episode(sDisplayTitle)
            if s != 0 and e != 0:
                oOutputParameterHandler.addParameter('sCat', '2')
                cGui.CONTENT = 'tvshows'
                oGuiElement.setMeta(2)
                oGuiElement.setCat(2)
            else:
                oOutputParameterHandler.addParameter('sCat', '1')
                cGui.CONTENT = 'movies'
                oGuiElement.setMeta(1)
                oGuiElement.setCat(1)

            oGui.CreateSimpleMenu(oGuiElement, oOutputParameterHandler, 'cHosterGui', 'cHosterGui', 'play', addons.VSlang(29981))
            oGui.CreateSimpleMenu(oGuiElement, oOutputParameterHandler, 'cHome', 'cHome', 'deleteFromHistory', addons.VSlang(30413))
            oGui.addFolder(oGuiElement, oOutputParameterHandler)

        progress_.VSclose(progress_)
        if len(matchedrow) == 0:
            oGui.addText("Tvwatch2",'[COLOR khaki]' + addons.VSlang(29999) + '[/COLOR]')
            oGui.setEndOfDirectory(50)
        else:
            oGui.setEndOfDirectory(500)

        if addons.getSetting('do_not_show_hint_continue_watching') != "true":
            text = "Appuyez longtemps sur un item et choisissez: \n"
            text += "\"Regarder maintenant\" pour démarrer la vidéo tout de suite !\n\n"
            text += "Ne plus afficher ce message ?"
            result = dialog().VSyesno(text, "Astuce")
            if result == 1:
                addons.setSetting('do_not_show_hint_continue_watching', 'true')

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
        cHome.deleteFromHistory = self.deleteFromHistory
        cGui.createContexMenuWatch = self.createContexMenuWatch
        cGui.addHost = cGui.addFolder
        cRechercheHandler.__dict__['_cRechercheHandler__getFileNamesFromFolder'] = self.getServers

        # Patch method showHoster of cHosterGui
        save_showHoster = cHosterGui.showHoster
        def new_showHoster(hos, oGui, oHoster, sMediaUrl, sThumbnail, bGetRedirectUrl = False):
            sDisplayName = oHoster.getDisplayName()
            sMovieTitle = oHoster.getFileName()

            if "uptostream" in sDisplayName.lower() or "uptobox" in sDisplayName.lower():
                sDisplayName = sDisplayName[:sDisplayName.rfind("[COLOR ")]
            if "uptostream" in sMovieTitle.lower() or "uptobox" in sMovieTitle.lower():
                sMovieTitle = sMovieTitle[:sMovieTitle.rfind("[COLOR ")]

            tvshow = False
            if "saison" in sDisplayName.lower() and "episode" in sDisplayName.lower():
                s, e, t = get_season_episode(sDisplayName)
                if s != 0 and e != 0:
                    sMovieTitle = t.strip()
                    tvshow = True
            elif "saison" in sMovieTitle.lower() and "episode" in sMovieTitle.lower():
                s, e, t = get_season_episode(sMovieTitle)
                if s != 0 and e != 0:
                    sDisplayName = sMovieTitle
                    sMovieTitle = t.strip()
                    tvshow = True
            elif sDisplayName.strip() != sMovieTitle.strip():
                s, e, t = get_season_episode(sMovieTitle + " " + sDisplayName)
                if s != 0 and e != 0:
                    sDisplayName = sMovieTitle.strip() + " " + sDisplayName.strip()
                    sMovieTitle = t.strip()
                    tvshow = True

            oDb = cDb()
            sDisplayName = oDb.str_conv(sDisplayName.strip())
            sMovieTitle = oDb.str_conv(sMovieTitle.strip())
            oHoster.__dict__['_cHoster__sDisplayName'] = sDisplayName.strip()
            oHoster.__dict__['_cHoster__sFileName'] = sMovieTitle.strip()

            if tvshow:
                VSlog(sDisplayName + ": type=tvshow")
                meta = {}
                meta["display"] = sDisplayName
                meta["title"] = sMovieTitle
                meta["url"] = sMediaUrl
                self.insert_tvshows(meta)
            else:
                VSlog(sDisplayName + ": type=movie")

            return save_showHoster(hos, oGui, oHoster, sMediaUrl, sThumbnail, bGetRedirectUrl)
        cHosterGui.showHoster = new_showHoster

        # Patch method play of cHosterGui
        save_play_hoster = cHosterGui.play
        def new_play_hoster(hoster):
            oInputParameterHandler = cInputParameterHandler()
            sFileName = oInputParameterHandler.getValue('sFileName')
            sDisplayName = oInputParameterHandler.getValue('sTitle')
            sThumbnail = xbmc.getInfoLabel('ListItem.Art(thumb)')

            current_saison, current_episode, t = get_season_episode(sDisplayName)

            if "saison" in sFileName.lower():
                a = sFileName.lower().find("saison")
                sFileName = sFileName[:a]
                VSlog("ERROR: new_play_hoster saison in sFileName")

            matchedrow = self.get_tvshows(sFileName)

            if current_saison == 0 or current_episode == 0 or len(matchedrow) < 2:
                VSlog("Disable NextUp")
                set_property('enableNextUp', 'false')
                return save_play_hoster(hoster)
            else:
                VSlog("Enable NextUp")
                set_property('enableNextUp', 'true')

                episodes = []
                for aEntry in matchedrow:
                    episode = {}
                    episode["sMediaUrl"] = UnquotePlus(aEntry[3])
                    episode["sHosterIdentifier"] = episode["sMediaUrl"][episode["sMediaUrl"].find('//')+len('//'):].split(".")[0]
                    episode["sDisplayName"] = str_deconv(aEntry[1])
                    episode["sMovieTitle"] = str_deconv(aEntry[2])

                    episode["saison"], episode["episode"], t = get_season_episode(episode["sDisplayName"])

                    if episode["saison"] == current_saison:
                        if episode["episode"] >= current_episode:
                            episodes.append(episode)

                episodes_sorted = []
                if len(episodes) > 0:
                    episodes_sorted = sorted(episodes, key=lambda k: k['episode'])
                else:
                    VSlog("Error1 => Disable NextUp")
                    set_property('enableNextUp', 'false')
                    return save_play_hoster(hoster)

                inputParams = oInputParameterHandler.getAllParameter()
                count = 0
                for episode in episodes_sorted:
                    count += 1
                    inputParams['sFileName'] = Unquote(episode["sMovieTitle"])
                    inputParams['title'] = Unquote(episode["sDisplayName"])
                    inputParams['sDisplayName'] = Unquote(episode["sDisplayName"])
                    inputParams['sMediaUrl'] = Unquote(episode["sMediaUrl"])
                    inputParams['sHosterIdentifier'] = Unquote(episode["sHosterIdentifier"])
                    inputParams['sTitle'] = Unquote(episode["sDisplayName"])
                    inputParams['siteUrl'] = Unquote(episode["sMediaUrl"])
                    inputParams['sThumbnail'] = Unquote(sThumbnail)

                    argument = '?'
                    for param, value in inputParams.items():
                        argument += param + '=' + value + '&'
                    sys.argv[2] = argument[:-1]

                    if count >= len(episodes_sorted):
                        VSlog("Error2 => Disable NextUp")
                        set_property('enableNextUp', 'false')

                    if not save_play_hoster(hoster):
                        break

        cHosterGui.play = new_play_hoster

        # Patch method CreateSimpleMenu of cGui
        save_CreateSimpleMenu = cGui.CreateSimpleMenu
        def new_CreateSimpleMenu(gui, oGuiElement, oOutputParameterHandler, sFile, sName, sFunction, sTitle):
            # if sFunction != 'UptomyAccount' and sFunction != 'setLibrary':
            if sFunction != 'setLibrary':
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
            URL = upto.getUrl()
            FILE_CODE = ""
            for code in URL.split("/"):
                if len(code) == 12:
                    FILE_CODE = code
                    break
            USR_TOKEN = "e84e2bdf19d127b4e624eed2c83bfd871tgrq"
            URL = "https://uptobox.com/api/link"
            PARAMS = {'token':USR_TOKEN, 'file_code':FILE_CODE}
            try:
                r = requests.get(url = URL, params = PARAMS)
                data = r.json()
                result = True, data['data']['dlLink']
            except Exception as err:
                VSlog("Exception getMediaLinkByUserToken: {0}".format(err))
                VSlog(data)
                result = False, False
            return result
        uptostream.cHoster.getMediaLink = getMediaLinkByUserToken
        uptobox.cHoster.getMediaLink = getMediaLinkByUserToken

        # Patch method run of cPlayer
        save_run = cPlayer.run
        def new_run(player, oGuiElement, sTitle, sUrl):
            try:

                player.seek_Time = 0.0
                if '.m3u' not in sUrl:
                    matchedrow = self.get_seekTime(player.sTitle)
                    for aEntry in matchedrow:
                        try:
                            player.seek_Time = float(aEntry[2])
                        except:
                            player.seek_Time = 0.0

                res = save_run(player, oGuiElement, sTitle, sUrl)

                if '.m3u' not in sUrl:
                    if player.totalTime > 0:
                        if float('%.2f' % (player.currentTime / player.totalTime)) > 0.90:
                            player.currentTime = 0.0
                    self.set_seekTime(player.sTitle, str(int(player.currentTime)))
                    player.currentTime = 0.0

                    if "saison" in sTitle.lower():
                        a = sTitle.lower().find("saison")
                        sTitle = sTitle[:a]
                        VSlog("ERROR: new_run saison in sTitle")

                    meta = {}
                    meta['title'] = sTitle
                    meta['display'] = player.sTitle
                    meta['url'] = player.sSite
                    meta['icon'] = player.sThumbnail

                    self.insert_resume(meta)

            except Exception as err:
                VSlog("Exception new_run: {0}".format(err))
            return res
        cPlayer.run = new_run

    def createContexMenuWatch(self, oGuiElement, oOutputParameterHandler= ''):
        return

    def searchOnCurrentServer(self):
        oGui = cGui()
        oInputParameterHandler = cInputParameterHandler()
        sSearchText = oInputParameterHandler.getValue('searchtext')
        sCat = oInputParameterHandler.getValue('sCat')

        if sCat == "1" and self.server_search_movies != None:
            sUrl = self.server_search_movies[0]
        elif sCat == "2" and self.server_search_series != None:
            sUrl = self.server_search_series[0]
        else:
            sUrl = self.server_search[0]

        if sSearchText:
            sUrl = sUrl + Quote(sSearchText)
            self.server_process_function(sUrl)
            oGui.setEndOfDirectory(50)

    def deleteFromHistory(self):
        oInputParameterHandler = cInputParameterHandler()
        self.del_resume(oInputParameterHandler.getValue('sMovieTitle'))
        VSupdate()

    def insert_resume(self, meta):
        oDb = cDb()

        title = oDb.str_conv(meta['title'])
        title = str_conv(title) #sMovieTitle

        display = oDb.str_conv(meta['display'])
        display = str_conv(display) #sDisplayName

        url = QuotePlus(meta['url'])
        icon = QuotePlus(meta['icon'])

        try:
            ex = 'INSERT INTO myResume (title, display, url, icon) VALUES (?, ?, ?, ?)'
            oDb.dbcur.execute(ex, (title, display, url, icon))
            oDb.db.commit()
            VSlog('SQL INSERT myResume Successfully')
        except Exception, e:
            if 'UNIQUE constraint failed' in e.message:
                ex = "UPDATE myResume set title = '%s', display = '%s', url= '%s', icon= '%s' WHERE title = '%s'" % (title, display, url, icon, title)
                oDb.dbcur.execute(ex)
                oDb.db.commit()
                VSlog('SQL UPDATE myResume Successfully')
            else:
                VSlog('SQL ERROR insert_resume: ' + str(e.message))

    def get_resume(self):
        oDb = cDb()
        try:
            # oDb.dbcur.execute("DELETE FROM myResume")
            # oDb.db.commit()
            sql_select = "SELECT * FROM myResume"
            oDb.dbcur.execute(sql_select)
            matchedrow = oDb.dbcur.fetchall()
            return matchedrow
        except Exception, e:
            VSlog('SQL ERROR GET myResume: ' + str(e.message))
            return []

    def del_resume(self, sMovieTitle):
        oDb = cDb()

        title = oDb.str_conv(sMovieTitle)
        title = str_conv(title)

        try:
            sql_select = "DELETE FROM myResume WHERE title = '%s'" % title
            oDb.dbcur.execute(sql_select)
            oDb.db.commit()
        except Exception, e:
            VSlog('SQL ERROR del_resume: ' + str(e.message))

    def insert_tvshows(self, meta):
        oDb = cDb()

        url = QuotePlus(meta['url']) #sMediaUrl

        title = oDb.str_conv(meta['title'])
        title = str_conv(title) #sMovieTitle

        display = oDb.str_conv(meta['display'])
        display = str_conv(display) #sDisplayName

        try:
            ex = 'INSERT INTO tvshows (display, title, url) VALUES (?, ?, ?)'
            oDb.dbcur.execute(ex, (display, title, url))
            oDb.db.commit()
            VSlog('SQL INSERT tvshows Successfully')
        except Exception, e:
            if 'UNIQUE constraint failed' in e.message:
                ex = "UPDATE tvshows set display = '%s', title = '%s', url= '%s' WHERE display = '%s'" % (display, title, url, display)
                oDb.dbcur.execute(ex)
                oDb.db.commit()
                VSlog('SQL UPDATE tvshows Successfully')
            else:
                VSlog('SQL ERROR insert_tvshows: ' + str(e.message))

    def get_tvshows(self, sMovieTitle):
        oDb = cDb()

        title = oDb.str_conv(sMovieTitle)
        title = str_conv(title)

        try:
            sql_select = "SELECT * FROM tvshows WHERE title = '%s'" % title
            oDb.dbcur.execute(sql_select)
            matchedrow = oDb.dbcur.fetchall()
            return matchedrow
        except Exception, e:
            VSlog('SQL ERROR get_tvshows: ' + str(e.message))
            return []

    def set_seekTime(self, sDisplayName, time):
        oDb = cDb()

        display = oDb.str_conv(sDisplayName)
        display = str_conv(display) #sDisplayName
        # seekTime = oDb.str_conv(seekTime) #seekTime

        try:
            ex = 'INSERT INTO seekTime (display, time) VALUES (?, ?)'
            oDb.dbcur.execute(ex, (display, time))
            oDb.db.commit()
            VSlog('SQL INSERT set_seekTime Successfully')
        except Exception, e:
            if 'UNIQUE constraint failed' in e.message:
                ex = "UPDATE seekTime set display = '%s', time = '%s' WHERE display = '%s'" % (display, time, display)
                oDb.dbcur.execute(ex)
                oDb.db.commit()
                VSlog('SQL UPDATE set_seekTime Successfully')
            else:
                VSlog('SQL ERROR set_seekTime: ' + str(e.message))

    def get_seekTime(self, sDisplayName):
        oDb = cDb()

        display = oDb.str_conv(sDisplayName)
        display = str_conv(display)

        try:
            sql_select = "SELECT * FROM seekTime WHERE display = '%s'" % display
            oDb.dbcur.execute(sql_select)
            matchedrow = oDb.dbcur.fetchall()
            return matchedrow
        except Exception, e:
            VSlog('SQL ERROR get_tvshows: ' + str(e.message))
            return []
