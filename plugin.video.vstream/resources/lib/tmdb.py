# -*- coding: utf-8 -*-
#Code de depart par AnthonyBloomer
#Modif pour vStream
#https://github.com/Kodi-vStream/venom-xbmc-addons/

from resources.lib.comaddon import addon, dialog, VSlog, xbmc
from urllib import quote_plus, urlopen
import json, urllib2
import xbmcvfs

try:
    from sqlite3 import dbapi2 as sqlite
    VSlog('SQLITE 3 as DB engine')
except:
    from pysqlite2 import dbapi2 as sqlite
    VSlog('SQLITE 2 as DB engine')


# https://developers.themoviedb.org/3
#xbmc.log(str(year), xbmc.LOGNOTICE)

TMDB_GENRES = {
    28:'Action', 12:'Aventure', 16:'Animation', 35:'Comédie', 80:'Crime',99:'Documentaire', 18:'Drame',
    10751:'Familial', 14:'Fantastique', 36:'Histoire', 27:'Horreur', 10402:'Musique', 9648:'Mystère',
    10749:'Romance', 878:'Science-Fiction', 10770:'Téléfilm', 53:'Thriller', 10752:'Guerre', 37:'Western'}


class cTMDb:
    URL = 'http://api.themoviedb.org/3/'
    CACHE = 'special://userdata/addon_data/plugin.video.tvwatch2/video_cache.db'
    #important seul xbmcvfs peux lire le special
    REALCACHE = xbmc.translatePath(CACHE).decode('utf-8')
    
    ADDON = addon()
    DIALOG = dialog()

    def __init__(self, api_key = '', debug = False, lang = 'fr'):

        self.api_key = self.ADDON.getSetting('api_tmdb')
        self.debug = debug
        self.lang = lang
        self.poster = 'https://image.tmdb.org/t/p/%s' % self.ADDON.getSetting('poster_tmdb')
        self.fanart = 'https://image.tmdb.org/t/p/%s' % self.ADDON.getSetting('backdrop_tmdb')
        #self.cache = cConfig().getFileCache()

        try:
            #if not os.path.exists(self.cache):
            if not xbmcvfs.exists(self.CACHE):
                #f = open(self.cache, 'w')
                #f.close()
                self.db = sqlite.connect(self.REALCACHE)
                self.db.row_factory = sqlite.Row
                self.dbcur = self.db.cursor()
                self.__createdb()
                return
        except:
            VSlog('Erreur: Impossible d ecrire sur %s' % self.REALCACHE)
            pass

        try:
            self.db = sqlite.connect(self.REALCACHE)
            self.db.row_factory = sqlite.Row
            self.dbcur = self.db.cursor()
        except:
            VSlog('Erreur: Impossible de ce connecter sur %s' % self.REALCACHE )
            pass

    def __createdb(self):

        sql_create = "CREATE TABLE IF NOT EXISTS movie ("\
                           "imdb_id TEXT, "\
                           "tmdb_id TEXT, "\
                           "title TEXT, "\
                           "year INTEGER,"\
                           "director TEXT, "\
                           "writer TEXT, "\
                           "tagline TEXT, "\
                           "credits TEXT,"\
                           "vote_average FLOAT, "\
                           "vote_count TEXT, "\
                           "runtime TEXT, "\
                           "overview TEXT,"\
                           "mpaa TEXT, "\
                           "premiered TEXT, "\
                           "genre TEXT, "\
                           "studio TEXT,"\
                           "status TEXT,"\
                           "poster_path TEXT, "\
                           "trailer TEXT, "\
                           "backdrop_path TEXT,"\
                           "playcount INTEGER,"\
                           "UNIQUE(imdb_id, tmdb_id, title, year)"\
                           ");"
        try:
            self.dbcur.execute(sql_create)
        except:
            VSlog('Erreur: ne peux pas creer de table')

        sql_create = "CREATE TABLE IF NOT EXISTS tvshow ("\
                           "imdb_id TEXT, "\
                           "tmdb_id TEXT, "\
                           "title TEXT, "\
                           "year INTEGER,"\
                           "director TEXT, "\
                           "writer TEXT, "\
                           "credits TEXT,"\
                           "vote_average FLOAT, "\
                           "vote_count TEXT, "\
                           "runtime TEXT, "\
                           "overview TEXT,"\
                           "mpaa TEXT, "\
                           "premiered TEXT, "\
                           "genre TEXT, "\
                           "studio TEXT,"\
                           "status TEXT,"\
                           "poster_path TEXT,"\
                           "trailer TEXT, "\
                           "backdrop_path TEXT,"\
                           "playcount INTEGER,"\
                           "UNIQUE(imdb_id, tmdb_id, title)"\
                           ");"

        self.dbcur.execute(sql_create)

        sql_create = "CREATE TABLE IF NOT EXISTS season ("\
                           "imdb_id TEXT, "\
                           "tmdb_id TEXT, " \
                           "season INTEGER, "\
                           "year INTEGER,"\
                           "premiered TEXT, "\
                           "poster_path TEXT,"\
                           "playcount INTEGER,"\
                           "UNIQUE(imdb_id, tmdb_id, season)"\
                           ");"

        self.dbcur.execute(sql_create)

        sql_create = "CREATE TABLE IF NOT EXISTS episode ("\
                           "imdb_id TEXT, "\
                           "tmdb_id TEXT, "\
                           "episode_id TEXT, "\
                           "season INTEGER, "\
                           "episode INTEGER, "\
                           "title TEXT, "\
                           "director TEXT, "\
                           "writer TEXT, "\
                           "overview TEXT, "\
                           "vote_average FLOAT, "\
                           "premiered TEXT, "\
                           "poster_path TEXT, "\
                           "playcount INTEGER, "\
                           "UNIQUE(imdb_id, tmdb_id, episode_id, title)"\
                           ");"

        self.dbcur.execute(sql_create)
        VSlog('table creee')

    def __del__(self):
        ''' Cleanup db when object destroyed '''
        try:
            self.dbcur.close()
            self.db.close()
        except:
            pass


    def getToken(self):

        result = self._call('authentication/token/new', '')

        total = len(result)

        if (total > 0):
            #self.__Token  = result['token']
            url = 'https://www.themoviedb.org/authenticate/'
            sText = (self.ADDON.VSlang(30421)) % (url, result['request_token'] )

            oDialog = self.DIALOG.VSyesno(sText)
            if (oDialog == 0):
                return False

            if (oDialog == 1):
                
                #print url
                result = self._call('authentication/session/new', 'request_token=' + result['request_token'])

                if 'success' in result and result['success']:
                    self.ADDON.setSetting('tmdb_session', str(result['session_id']))
                    self.DIALOG.VSinfo(self.ADDON.VSlang(30000))
                    return
                else:
                    self.DIALOG.VSerror('Erreur' + self.ADDON.VSlang(30000))
                    return


            #xbmc.executebuiltin('Container.Refresh')
            return
        return

    #cherche dans les films ou serie l'id par le nom return ID ou FALSE
    def get_idbyname(self, name, year = '', mediaType = 'movie', page = 1):

        if year:
            term = quote_plus(name) + '&year=' + year
        else:
            term = quote_plus(name)

        meta = self._call('search/' + str(mediaType), 'query=' + term + '&page=' + str(page))
        #teste sans l'année
        if 'errors' not in meta and 'status_code' not in meta:
            if 'total_results' in meta and meta['total_results'] == 0 and year:
                    #meta = self.get_movie_idbyname(name,'')
                    meta = self.search_movie_name(name, '')

            #cherche 1 seul resultat
            if 'total_results' in meta and meta['total_results'] != 0:
                tmdb_id = meta['results'][0]['id']
                return tmdb_id
        else:
            return False

        return False

    # Search for movies by title.
    def search_movie_name(self, name, year = '', page = 1):

        if year:
            term = quote_plus(name) + '&year=' + year
        else:
            term = quote_plus(name)

        meta = self._call('search/movie', 'query=' + term + '&page=' + str(page))
        
        # teste sans l'année si pas trouvé
        if 'errors' not in meta and 'status_code' not in meta:
            if 'total_results' in meta and meta['total_results'] == 0 and year:
                meta = self.search_movie_name(name, '')

            # cherche 1 seul resultat
            if 'total_results' in meta and meta['total_results'] != 0:
                tmdb_id = meta['results'][0]['id']
                #cherche toutes les infos
                meta = self.search_movie_id(tmdb_id)
        else:
            meta = {}

        return meta

            # Search for TV shows by title.
    def search_tvshow_name(self, name, year = '', page = 1):

        if year:
            term = quote_plus(name) + '&year=' + year
        else:
            term = quote_plus(name)

        meta = self._call('search/tv', 'query=' + term + '&page=' + str(page))
        if 'errors' not in meta and 'status_code' not in meta:

            if 'total_results' in meta and meta['total_results'] == 0 and year:
                meta = self.search_tvshow_name(name, '')
            #cherche 1 seul resultat
            if 'total_results' in meta and meta['total_results'] != 0:
                tmdb_id = meta['results'][0]['id']
                #cherche toutes les infos
                meta = self.search_tvshow_id(tmdb_id)
        else:
            meta = {}

        return meta

    # Get the basic movie information for a specific movie id.
    def search_movie_id(self, movie_id, append_to_response = 'append_to_response=trailers,credits'):
        result = self._call('movie/' + str(movie_id), append_to_response)
        result['tmdb_id'] = movie_id
        return result #obj(**self._call('movie/' + str(movie_id), append_to_response))

    # Get the primary information about a TV series by id.
    def search_tvshow_id(self, show_id, append_to_response = 'append_to_response=external_ids,credits'):
        result = self._call('tv/' + str(show_id), append_to_response)
        result['tmdb_id'] = show_id
        return result

    def _format(self, meta, name):
        _meta = {}
        _meta['imdb_id'] = ''
        _meta['tmdb_id'] = ''
        _meta['tvdb_id'] = ''
        _meta['title'] = name
        _meta['media_type'] = ''
        _meta['rating'] = 0
        _meta['votes'] = 0
        _meta['duration'] = 0
        _meta['plot'] = ''
        _meta['mpaa'] = ''
        _meta['premiered'] = ''
        _meta['year'] = ''
        _meta['trailer'] = ''
        _meta['trailer_url'] = ''
        _meta['genre'] = ''
        _meta['studio'] = ''
        _meta['status'] = ''
        _meta['credits'] = ''
        _meta['cast'] = []
        _meta['poster_path'] = ''
        _meta['cover_url'] = ''
        _meta['backdrop_path'] = ''
        _meta['backdrop_url'] = ''
        _meta['episode'] = 0
        _meta['playcount'] = 0

        if 'title' in meta and meta['title']:
            _meta['title'] = meta['title']
        elif 'name' in meta and meta['name']:
            _meta['title'] = meta['name']

        if 'id' in meta:
            _meta['tmdb_id'] = meta['id']
        if 'tmdb_id' in meta:
            _meta['tmdb_id'] = meta['tmdb_id']
        if 'imdb_id' in meta:
            _meta['imdb_id'] = meta['imdb_id']
        elif 'external_ids' in meta:
            _meta['imdb_id'] = meta['external_ids']['imdb_id']
        if 'mpaa' in meta:
            _meta['mpaa'] = meta['mpaa']
        if 'media_type' in meta:
            _meta['media_type'] = meta['media_type']


        if 'release_date' in meta:
            _meta['release_date'] = meta['release_date']
        if 'premiered' in meta and meta['premiered']:
            _meta['premiered'] = meta['premiered']
        elif 's_premiered' in meta and meta['s_premiered']:
            _meta['premiered'] = meta['s_premiered']

        if 'year' in meta:
            _meta['year'] = meta['year']
        elif 's_year' in meta:
            _meta['year'] = meta['s_year']
        else:
            try:
                if 'release_date' in _meta and _meta['release_date']:
                    _meta['year'] = int(_meta['release_date'][:4])
                elif 'premiered' in _meta and _meta['premiered']:
                    _meta['year'] = int(_meta['premiered'][:4])
                elif 'first_air_date' in meta and meta['first_air_date']:
                    _meta['year'] = int(meta['first_air_date'][:4])
                elif 'air_date' in meta and meta['air_date']:
                    _meta['year'] = int(meta['air_date'][:4])
            except: pass

        if 'rating' in meta:
            _meta['rating'] = meta['rating']
        elif 'vote_average' in meta:
            _meta['rating'] = meta['vote_average']
        if 'votes' in meta:
            _meta['votes'] = meta['votes']
        elif 'vote_count' in meta:
            _meta['votes'] = meta['vote_count']

        try:
            duration = 0
            if 'runtime' in meta and meta['runtime']:
                duration = int(meta['runtime'])
            elif 'episode_run_time' in meta and meta['episode_run_time']:
                duration = int(meta['episode_run_time'][0])
            if duration > 240:  # En secondes au lieu de minutes
                duration /= 60
            _meta['duration'] = duration
        except:
            _meta['duration'] = 0

        if 'overview' in meta:
            _meta['plot'] = meta['overview']

        if 'studio' in meta:
            _meta['studio'] = meta['studio']
        elif 'production_companies' in meta:
            _meta['studio'] = ''
            for studio in meta['production_companies']:
                if _meta['studio'] == '':
                    _meta['studio'] += studio['name']
                else:
                    _meta['studio'] += ' / '+studio['name']

        if 'genre' in meta:
            listeGenre = meta['genre']
            if '{' in listeGenre:
                meta['genres'] = eval(listeGenre)
            else:
                _meta['genre'] = listeGenre
        if 'genres' in meta:
#             _meta['genre'] = ''
            for genre in meta['genres']:
                if _meta['genre'] == '':
                    _meta['genre'] += genre['name']
                else:
                    _meta['genre'] += ' / '+genre['name']
        elif 'genre_ids' in meta:
            genres = self.getGenresFromIDs(meta['genre_ids'])
            _meta['genre'] = ''
            for genre in genres:
                if _meta['genre'] == '':
                    _meta['genre'] += genre
                else:
                    _meta['genre'] += ' / '+genre

        if 'trailer' in meta:
            _meta['trailer'] = meta['trailer']
            if 'plugin:' in _meta['trailer']:
                trailer_id = meta['trailer'].split('=')[2]
                _meta['trailer_url'] = 'http://www.youtube.com/watch?v='+trailer_id
        else:
            try:    # Recherche de la BA en français
                trailer_id = ''
                trailers = meta['trailers']['youtube']
                for trailer in trailers:
                    if trailer['type'] == 'Trailer':
                        if 'VF' in trailer['name']:
                            trailer_id = trailer['source']
                            break
                # pas de trailer français, on prend le premier
                if not trailer_id:
                    trailer_id = meta['trailers']['youtube'][0]['source']
                _meta['trailer_url'] = 'http://www.youtube.com/watch?v='+trailer_id
                _meta['trailer'] = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s' % trailer_id
            except:
                pass


        if 'backdrop_path' in meta and meta['backdrop_path']:
            _meta['backdrop_path'] = meta['backdrop_path']
            _meta['backdrop_url'] = self.fanart+str(meta['backdrop_path'])
        if 'poster_path' in meta and meta['poster_path']:
            _meta['poster_path'] = meta['poster_path']
            _meta['cover_url'] = self.poster+str(meta['poster_path'])
        #special saisons
        if 's_poster_path' in meta and meta['s_poster_path']:
            _meta['poster_path'] = meta['s_poster_path']
            _meta['cover_url'] = self.poster+str(meta['s_poster_path'])

        if not 'playcount' in meta:
            _meta['playcount'] = 0
        else:
            _meta['playcount'] = meta['playcount']
            if _meta['playcount'] == 6:     # Anciennement 6 = unwatched
                _meta['playcount'] = 0
                
        if 'tagline' in meta:
            _meta['tagline'] = meta['tagline']

        if 'status' in meta:
            _meta['status'] = meta['status']

        # if 'cast' in meta:
            # _meta['cast'] = json.loads(_meta['cast'])
        if 'credits' in meta and meta['credits']:
            listCredits = eval(str(meta['credits']))
#           _meta['credits'] = str(meta['credits']).strip('[]')
            licast = []
            for cast in listCredits['cast']:
                licast.append((cast['name'], cast['character'], self.poster + str(cast['profile_path']), str(cast['id'])))
                #licast.append((cast['name'], cast['character'], self.poster + str(cast['profile_path'])))
            _meta['cast'] = licast

            _meta['writer'] = ''
            for crew in listCredits['crew']:
                if crew['job'] == 'Director':
                    _meta['director'] = crew['name']
                else:
                    if _meta['writer'] == '':
                        _meta['writer'] += '%s (%s)' % (crew['job'], crew['name'])
                    else:
                        _meta['writer'] += ' / %s (%s)' % (crew['job'], crew['name'])

        return _meta

    def _clean_title(self, title):
        title= title.replace(' ', '')
        title = title.lower()
        return title


    def _cache_search(self, media_type, name, tmdb_id = '', year = '', season = '', episode = ''):
        if media_type == 'movie':
            sql_select = 'SELECT * FROM movie'
            if tmdb_id:
                sql_select = sql_select + ' WHERE tmdb_id = \'%s\'' % tmdb_id
            else:
                sql_select = sql_select + ' WHERE title = \'%s\'' % name

            if year:
                sql_select = sql_select + ' AND year = %s' % year

        elif media_type == 'tvshow':

            sql_select = 'SELECT * FROM tvshow'
            if season:
                sql_select = 'SELECT *, season.poster_path as s_poster_path, season.premiered as s_premiered, season.year as s_year FROM tvshow LEFT JOIN season ON tvshow.imdb_id = season.imdb_id'
            if tmdb_id:
                sql_select = sql_select + ' WHERE tvshow.tmdb_id = \'%s\'' % tmdb_id
            else:
                sql_select = sql_select + ' WHERE tvshow.title = \'%s\'' % name

            if year:
                sql_select = sql_select + ' AND tvshow.year = %s' % year

            if season:
                sql_select = sql_select + ' AND season.season = \'%s\'' % season

        #print sql_select
        try:
            self.dbcur.execute(sql_select)
            matchedrow = self.dbcur.fetchone()
        except Exception, e:
            VSlog('************* Error selecting from cache db: %s' % e, 4)
            return None

        if matchedrow:
            VSlog('Found meta information by name in cache table')
            return dict(matchedrow)
        else:
            VSlog('No match in local DB')
            return None

    def _cache_save(self, meta, name, media_type, season, year):

        #ecrit les saisons dans la BDD
        if 'seasons' in meta:
            self._cache_save_season(meta, season)
            del meta['seasons']

        #ecrit movie et tvshow dans la BDD
        # year n'est pas forcement l'année du film mais l'année utilisée pour la recherche
        try:
            sql = 'INSERT INTO %s (imdb_id, tmdb_id, title, year, credits, vote_average, vote_count, runtime, overview, mpaa, premiered, genre, studio, status, poster_path, trailer, backdrop_path, playcount) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)' % media_type
            self.dbcur.execute(sql, (meta['imdb_id'], meta['tmdb_id'], name, year, meta['credits'], meta['rating'], meta['votes'], meta['duration'], meta['plot'], meta['mpaa'], meta['premiered'], meta['genre'], meta['studio'], meta['status'], meta['poster_path'], meta['trailer'], meta['backdrop_path'], 0))
            self.db.commit()
            VSlog('SQL INSERT Successfully')
        except Exception, e:
            VSlog('SQL ERROR INSERT')
            pass

    def _cache_save_season(self, meta, season):

        for s in meta['seasons']:
            if  s['season_number'] != None and ('%02d' % int(s['season_number'])) == season:
                meta['s_poster_path']= s['poster_path']
                meta['s_premiered'] = s['air_date']
                meta['s_year'] = s['air_date']

            #xbmc.log(str(s['season_number']) + str(season))
            try:
                sql = 'INSERT INTO season (imdb_id, tmdb_id, season, year, premiered, poster_path, playcount) VALUES (?, ?, ?, ?, ?, ?, ?)'
                self.dbcur.execute(sql, (meta['imdb_id'], s['id'], s['season_number'], s['air_date'], s['air_date'], s['poster_path'], 6))

                self.db.commit()
                VSlog('SQL INSERT Successfully')
            except Exception, e:
                VSlog('SQL ERROR INSERT')
                pass

    def get_meta(self, media_type, name, imdb_id = '', tmdb_id = '', year = '', season = '', episode = '', update = False):
        '''
        Main method to get meta data for movie or tvshow. Will lookup by name/year
        if no IMDB ID supplied.

        Args:
            media_type (str): 'movie' or 'tvshow'
            name (str): full name of movie/tvshow you are searching
        Kwargs:
            imdb_id (str): IMDB ID
            tmdb_id (str): TMDB ID
            year (str): 4 digit year of video, recommended to include the year whenever possible
                        to maximize correct search results.
            season (int)
            episode (int)

        Returns:
            DICT of meta data or None if cannot be found.
        '''

        VSlog('Attempting to retrieve meta data for %s: %s %s %s %s' % (media_type, name, year, imdb_id, tmdb_id))

        #recherche dans la base de données
        if not update:
            meta = self._cache_search(media_type, self._clean_title(name), tmdb_id, year, season, episode)
            if meta:
                meta = self._format(meta, name)
                return meta

        #recherche online
        meta = {}
        if media_type=='movie':
            if tmdb_id:
                meta = self.search_movie_id(tmdb_id)
            elif name:
                meta = self.search_movie_name(name, year)
        elif media_type=='tvshow':
            if tmdb_id:
                meta = self.search_tvshow_id(tmdb_id)
            elif name:
                meta = self.search_tvshow_name(name, year)

        # transforme les metas si trouvé
        if meta and 'tmdb_id' in meta:
            meta = self._format(meta, name)
            # sauvegarde
            self._cache_save(meta, self._clean_title(name), media_type, season, year)
        else:   # initialise un meta vide
            meta = self._format(meta, name)

        return meta

    def getUrl(self, url, page = 1, term = ''):
        #return url api exemple 'movie/popular' page en cours
        try:
            if term:
                term = term + '&page=' + str(page)
            else:
                term = 'page=' + str(page)
            result = self._call(url, term)
        except:
            return False
        return result

    def _call(self, action, append_to_response):
        url = '%s%s?api_key=%s&%s&language=%s' % (self.URL, action, self.api_key, append_to_response, self.lang)
        #xbmc.log(str(url), xbmc.LOGNOTICE)
        response = urlopen(url)
        data = json.loads(response.read())
        return data

    def getPostUrl(self, action, post):

        tmdb_session = self.ADDON.getSetting('tmdb_session')
        if not tmdb_session:
            return

        sUrl = '%s%s?api_key=%s&session_id=%s' % (self.URL, action, self.api_key, tmdb_session)
        sPost = json.dumps(post)

        headers = {'Content-Type': 'application/json'}
        req = urllib2.Request(sUrl, sPost, headers)
        response = urllib2.urlopen(req)
        data = json.loads(response.read())
        return data

    # retourne la liste des genres en Texte, à partir des IDs
    def getGenresFromIDs(self, genresID):
        sGenres = []
        for gid in genresID:
            genre = TMDB_GENRES.get(gid)
            if genre:
                sGenres.append(genre)
        return sGenres