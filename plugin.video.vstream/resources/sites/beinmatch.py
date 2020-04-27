# -*- coding: utf-8 -*-

from resources.lib.comaddon import progress, dialog, VSlog
from resources.lib.gui.gui import cGui
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.gui.hoster import cHosterGui
from resources.lib.handler.inputParameterHandler import cInputParameterHandler
from resources.lib.handler.outputParameterHandler import cOutputParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.player import cPlayer
from resources.lib.util import Unquote, Quote, QuotePlus

SITE_IDENTIFIER = 'beinmatch'
SITE_NAME = '[COLOR orange]Sport Direct/Stream[/COLOR]'

URL_MAIN = "https://beinmatch.best/"
UA = 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/48.0.2564.116 Chrome/48.0.2564.116 Safari/537.36'

headers = {'User-Agent': UA, 'Accept': '*/*', 'Connection': 'keep-alive'}

sRootArt = 'special://home/addons/plugin.video.tvwatch2/resources/art/tv'

def find_between(s, first, last):
    try:
        if first == "**START**":
            start = 0
        else:
            start = s.index(first) + len(first)

        if last == "**END**":
            end = len(s)
        else:
            end = s.index(last, start)
    except:
        VSlog("ERROR in find_between")
        VSlog(s)
        VSlog(first)
        VSlog(last)
    return s[start:end], start, end

def getUrl(sHtmlContent, params_):
    params, start, end = find_between(sHtmlContent, "function goToMatch", "{")
    params = params.strip()
    func, start, end = find_between(sHtmlContent, "function goToMatch", "}")
    func, start, end = find_between(func, "window.location.assign(", ")")
    params_ = [str(s) for s in params_]
    exec('%s = %s' % (params, str(params_)))
    return eval(func)

def load():
    oGui = cGui()

    oRequestHandler = cRequestHandler(URL_MAIN)
    sHtmlContent = oRequestHandler.request()

    for i in range(sHtmlContent.count("headerRightSide")):
        data, start, end = find_between(sHtmlContent, "headerRightSide", "</div>")
        sHtmlContent = sHtmlContent[start:]

        icon = "tv.png"
        item = ""
        count = 1
        while ('"p%d"' % count) in data:
            d, start, end = find_between(data, ('"p%d">' % count), '</p>')
            if "مباريات اليوم" in d:
                d = "Matchs d'aujourd'hui"
                icon = "sport.png"
            if "أهداف وملخصات مباريات أمس" in d:
                d = "Buts et résumés des Matchs d'hier"
                icon = "replay.png"
            count += 1
            item += d + " "

        oOutputParameterHandler = cOutputParameterHandler()
        oOutputParameterHandler.addParameter('siteUrl', 'http://venom/')
        oOutputParameterHandler.addParameter('index', str(i))
        oOutputParameterHandler.addParameter('sCat', '6')
        oGui.addDir('beinmatch', 'category', item, icon, oOutputParameterHandler)

    oGui.setEndOfDirectory(50)

def category():
    oGui = cGui()

    oInputParameterHandler = cInputParameterHandler()
    index = oInputParameterHandler.getValue('index')
    index = int(index)

    oRequestHandler = cRequestHandler(URL_MAIN)
    sHtmlContent = oRequestHandler.request()
    sHtmlContent_c = sHtmlContent

    data = ""
    contentRightSideCount = sHtmlContent.count("contentRightSide")
    for i in range(contentRightSideCount):
        last = "**END**" if (i == contentRightSideCount - 1) else "contentRightSide"
        data, start, end = find_between(sHtmlContent, "contentRightSide", last)
        sHtmlContent = sHtmlContent[start:]

        if i == index:
            break

    save_data = data
    items = []
    countTabIndex = save_data.count('<table class="tabIndex">')
    for i in range(countTabIndex):
        last = "**END**" if (i == countTabIndex - 1) else '<table class="tabIndex">'
        data, start, end = find_between(save_data, '<table class="tabIndex">', last)
        save_data = save_data[start:]

        map = {}

        sUrl, start, end = find_between(data, "goToMatch", '">')
        sUrl = sUrl.replace(";","")
        sUrl = eval(sUrl)
        sUrl = getUrl(sHtmlContent_c, list(sUrl))

        team1, start, end = find_between(data, 'tdTeam">', '</td>')
        if ">" in team1 and "<" in team1: team1, start, end = find_between(team1, '>', '<')
        team2, start, end = find_between(data[end:], 'tdTeam">', '</td>')
        if ">" in team2 and "<" in team2: team2, start, end = find_between(team2, '>', '<')

        image1, start, end = find_between(data, 'tdFlag">', '</td>')
        image1, start, end = find_between(image1, 'http', ')')
        image1 = "http" + image1

        image2, start, end = find_between(data[end:], 'tdFlag">', '</td>')
        image2, start, end = find_between(image2, 'http', ')')
        image2 = "http" + image2

        time = ""
        if "GMT" in data:
            a = data.find("GMT") + len("GMT")
            b = data[:a].rfind(">") + len(">")
            time = data[b:a].strip()
        elif "جارية حاليا" in data:
            time = "(Live)"
        elif "إنتهت المباراة" in data:
            time = "(Ended)"

        map["team1"] = team1
        map["team2"] = team2
        map["image1"] = image1
        map["image2"] = image2
        map["sUrl"] = sUrl
        map["time"] = time

        items.append(map)

    if len(items) > 0:
        progress_ = progress().VScreate(SITE_NAME)

        total = len(items)
        count = -1
        for aEntry in items:
            count += 1
            progress_.VSupdate(progress_, total)
            if progress_.iscanceled():
                break

            title = aEntry["time"] + " " + aEntry["team1"] + " VS " + aEntry["team2"]
            oOutputParameterHandler = cOutputParameterHandler()
            oOutputParameterHandler.addParameter('siteUrl', aEntry["sUrl"])
            oOutputParameterHandler.addParameter('sMovieTitle', title)
            oOutputParameterHandler.addParameter('sThumbnail', aEntry["image1"])

            oGuiElement = cGuiElement()
            oGuiElement.setSiteName(SITE_IDENTIFIER)
            oGuiElement.setFunction('play__')
            oGuiElement.setTitle(title)
            oGuiElement.setFileName(title)
            oGuiElement.setIcon(aEntry["image1"])
            oGuiElement.setMeta(0)
            oGuiElement.setThumbnail(aEntry["image1"])
            oGuiElement.setDirectTvFanart()
            oGuiElement.setCat(6)

            oGui.createContexMenuBookmark(oGuiElement, oOutputParameterHandler)
            oGui.addFolder(oGuiElement, oOutputParameterHandler)

        progress_.VSclose(progress_)

    oGui.setEndOfDirectory()

def findSourceUrl(sHtmlContent):
    sHtmlContent, start, end = find_between(sHtmlContent, 'video-container', '</div>')

    if "<script>" in sHtmlContent:
        sUrl, start, end = find_between(sHtmlContent.replace(" ", ""), 'Player(', ')')
        sUrl, start, end = find_between(sUrl, 'source:"', '"')
        return True, sUrl
    elif "<iframe" in sHtmlContent:
        sUrl, start, end = find_between(sHtmlContent.replace(" ", ""), '<iframe', '>')
        sUrl, start, end = find_between(sUrl, 'src="', '"')
        return False, sUrl

def play__():  # Lancer les liens

    oInputParameterHandler = cInputParameterHandler()
    sUrl = oInputParameterHandler.getValue('siteUrl').replace('P_L_U_S', '+')
    sTitle = oInputParameterHandler.getValue('sMovieTitle')
    sThumbnail = oInputParameterHandler.getValue('sThumbnail')

    sUrl = sUrl.split("/")
    sUrl[-1] = Quote(sUrl[-1])
    sUrl = "/".join(sUrl)
    oRequestHandler = cRequestHandler(sUrl)
    sHtmlContent = oRequestHandler.request()

    res, sUrl = findSourceUrl(sHtmlContent)

    if not res:
        oGui = cGui()
        oHoster = cHosterGui().checkHoster(sUrl)
        if (oHoster != False):
            oHoster.setDisplayName(sTitle)
            oHoster.setFileName(sTitle)
            cHosterGui().showHoster(oGui, oHoster, sUrl, sThumbnail, force=True)

        oGui.setEndOfDirectory(50)
        return

    oGuiElement = cGuiElement()
    oGuiElement.setSiteName(SITE_IDENTIFIER)
    oGuiElement.setTitle(sTitle)
    sUrl = sUrl.replace(' ', '%20')
    oGuiElement.setMediaUrl(sUrl)
    oGuiElement.setThumbnail(sThumbnail)

    oPlayer = cPlayer()
    oPlayer.clearPlayList()
    oPlayer.addItemToPlaylist(oGuiElement)
    oPlayer.startPlayer()
