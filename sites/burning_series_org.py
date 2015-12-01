﻿# -*- coding: utf-8 -*-
from resources.lib.gui.gui import cGui
from resources.lib.util import cUtil
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.config import cConfig
from resources.lib import logger
import string
import json
from resources.lib.bs_finalizer import *

# Variablen definieren die "global" verwendet werden sollen
SITE_IDENTIFIER = 'burning_series_org'
SITE_NAME = 'Burning-Series'
SITE_ICON = 'burning_series.jpg'

URL_MAIN = 'http://www.bs.to/api/'
URL_COVER = 'http://s.bs.to/img/cover/%s.jpg|encoding=gzip'

# Hauptmenu erstellen
def load():
    logger.info("Load %s" % SITE_NAME)
    # instanzieren eines Objekts der Klasse cGui zur Erstellung eines Menus
    oGui = cGui()
    # Menueintrag, durch Instanzierung eines Objekts der Klasse cGuiElement, erzeugen und zum Menu (oGui) hinzufügen
    oGui.addFolder(cGuiElement('Alle Serien', SITE_IDENTIFIER, 'showSeries'))
    oGui.addFolder(cGuiElement('A-Z', SITE_IDENTIFIER, 'showCharacters'))
    oGui.addFolder(cGuiElement('Suche', SITE_IDENTIFIER, 'showSearch'))
    # Ende des Menus
    oGui.setEndOfDirectory()

def _getContent(urlPart):
    request = cRequestHandler(URL_MAIN + urlPart)
    mod_request(request, urlPart)
    return json.loads(request.request())

def showSearch():
    oGui = cGui()
    sSearchText = oGui.showKeyBoard()
    if not sSearchText: return
    _search(oGui, sSearchText)
    oGui.setEndOfDirectory()

def _search(oGui, sSearchText):
    params = ParameterHandler()
    series = _getContent("series")
    total = len(series)
    sSearchText = sSearchText.lower()
    for serie in series:
        sTitle = serie["series"].encode('utf-8')
        if sTitle.lower().find(sSearchText) == -1: continue
        guiElement = cGuiElement(sTitle, SITE_IDENTIFIER, 'showSeasons')
        guiElement.setMediaType('tvshow')
        guiElement.setThumbnail(URL_COVER % serie["id"])
        params.addParams({'seriesID' : str(serie["id"]), 'Title' : sTitle})
        oGui.addFolder(guiElement, params, iTotal = total)

def showCharacters():
    oGui = cGui()
    oGuiElement = cGuiElement()
    oParams = ParameterHandler()
    oGuiElement = cGuiElement('#', SITE_IDENTIFIER, 'showSeries')
    oParams.setParam('char','#')
    oGui.addFolder(oGuiElement, oParams)
    for letter in string.uppercase[:26]:
        oGuiElement = cGuiElement(letter, SITE_IDENTIFIER, 'showSeries')
        oParams.setParam('char',letter)
        oGui.addFolder(oGuiElement, oParams)
    # Ende des Menus
    oGui.setEndOfDirectory()

def showSeries():
    oGui = cGui()
    oParams = ParameterHandler()
    sChar = oParams.getValue('char')
    if sChar: sChar = sChar.lower()
    series = _getContent("series")
    total = len(series)
    for serie in series:
        sTitle = serie["series"].encode('utf-8')
        if sChar:
            if sChar == '#':
                if sTitle[0].isalpha(): continue
            elif sTitle[0].lower() != sChar: continue
        guiElement = cGuiElement(sTitle, SITE_IDENTIFIER, 'showSeasons')
        guiElement.setMediaType('tvshow')
        guiElement.setThumbnail(URL_COVER % serie["id"])
        # Load series description by iteration through the REST-Api (slow)
        #sDesc = _getContent("series/%d/1" % int(serie['id']))
        #guiElement.setDescription(sDesc['series']['description'].encode('utf-8'))
        #sStart = str(sDesc['series']['start'])
        #if sStart != 'None':
        #   guiElement.setYear(int(sDesc['series']['start']))
        oParams.addParams({'seriesID' : str(serie["id"]), 'Title' : sTitle})
        oGui.addFolder(guiElement, oParams, iTotal = total)

    oGui.setView('tvshows')
    oGui.setEndOfDirectory()

def showSeasons():
    oGui = cGui()
    params = ParameterHandler()
    sTitle = params.getValue('Title')
    seriesId = params.getValue('seriesID')
    sImdb = params.getValue('imdbID')

    logger.info("%s: show seasons of '%s' " % (SITE_NAME, sTitle))

    data = _getContent("series/%s/1" % seriesId)
    rangeStart = not int(data["series"]["movies"])
    total = int(data["series"]["seasons"])
    for i in range(rangeStart, total + 1):
        seasonNum = str(i)
        seasonTitle = 'Film(e)' if i is 0 else '%s - Staffel %s' %(sTitle, seasonNum)
        guiElement = cGuiElement(seasonTitle, SITE_IDENTIFIER, 'showEpisodes')
        guiElement.setMediaType('season')
        guiElement.setSeason(seasonNum)
        guiElement.setTVShowTitle(sTitle)

        params.setParam('Season', seasonNum)
        guiElement.setThumbnail(URL_COVER % data["series"]["id"])
        oGui.addFolder(guiElement, params, iTotal = total)
    oGui.setView('seasons')
    oGui.setEndOfDirectory()

def showEpisodes():
    oGui = cGui()
    oParams = ParameterHandler()
    sShowTitle = oParams.getValue('Title')
    seriesId = oParams.getValue('seriesID')
    sImdb = oParams.getValue('imdbID')
    sSeason = oParams.getValue('Season')

    logger.info("%s: show episodes of '%s' season '%s' " % (SITE_NAME, sShowTitle, sSeason))

    data = _getContent("series/%s/%s" % (seriesId, sSeason))
    total = len(data['epi'])
    for episode in data['epi']:
        title = "%d - " % int(episode['epi'])
        if episode['german']:
            title += episode['german'].encode('utf-8')
        else:
            title += episode['english'].encode('utf-8')
        guiElement = cGuiElement(title, SITE_IDENTIFIER, 'showHosters')
        guiElement.setMediaType('episode')
        guiElement.setSeason(data['season'])
        guiElement.setEpisode(episode['epi'])
        guiElement.setTVShowTitle(sShowTitle)
        guiElement.setThumbnail(URL_COVER % data["series"]["id"])

        oParams.setParam('EpisodeNr', episode['epi'])
        #oParams.setParam('siteUrl',sUrl+"/"+sSeason+"/"+episode['epi'])
        oGui.addFolder(guiElement, oParams, bIsFolder = False, iTotal = total)
    oGui.setView('episodes')
    oGui.setEndOfDirectory()

def showHosters():
    oParams= ParameterHandler()
    sTitle = oParams.getValue('Title')
    seriesId = oParams.getValue('seriesID')
    season = oParams.getValue('Season')
    episode = oParams.getValue('EpisodeNr')

    data = _getContent("series/%s/%s/%s" % (seriesId, season, episode))
    hosters = []
    for link in data['links']:
        hoster = dict()
        hoster['link'] = URL_MAIN + 'watch/' + link['id']
        hoster['name'] = link['hoster']
        hoster['displayedName'] = link['hoster']
        hosters.append(hoster)
    if hosters:
        hosters.append('getHosterUrl')
    return hosters

def getHosterUrl(sUrl = False):
    oParams = ParameterHandler()
    #sTitle = oParams.getValue('Title')
    #sHoster = oParams.getValue('Hoster')
    if not sUrl: sUrl = oParams.getValue('url')
    data = _getContent(sUrl.replace(URL_MAIN, ''))

    results = []
    result = {}
    result['streamUrl'] = data['fullurl']
    result['resolved'] = False
    results.append(result)
    return results
