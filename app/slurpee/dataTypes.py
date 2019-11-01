import xml.dom.minidom
import sqlite3

class TVShow():
    def __init__(self, id, name, path, filename, season, minepisode, enabled, tvdbid=0, enabled_override=0, email=None):
        if id is not None:
          self.id = int(id)
        else:
          self.id = None
        self.name = str(name)
        self.path = str(path)
        self.filename = str(filename)
        self.season = int(season)
        self.minepisode = int(minepisode)
        self.enabled = int(enabled)
        if enabled_override:
            self.enabled_override = 1
        else:
            self.enabled_override = 0
        if tvdbid:
            self.tvdbid = int(tvdbid)
        else:
            self.tvdbid = 0
        self.airedSeasons = {}
        self.notify_email = email

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self.__dict__)

    def toDict(self):
        return { 
          'id':self.id,
          'name':self.name,
          'path':self.path,
          'filename':self.filename,
          'season':self.season,
          'minepisode':self.season,
          'enabled':self.enabled,
          'tvdbid':self.tvdbid,
          'enabled_override':self.enabled_override,
          'airedSeasons':self.airedSeasons,
          'notify_email':self.notify_email
        }

class ShowDB():
    def __init__(self, dbpath, keepOpen=False):
        self.dbpath = dbpath
        self.db = None
        self.keepOpen = keepOpen
        if keepOpen:
            self.db = sqlite3.connect(self.dbpath)

    def __delete__(self):
        if self.keepOpen:
            self.db.close()

    def _open(self):
        if not self.keepOpen:
            self.db = sqlite3.connect(self.dbpath)
        return self.db

    def _close(self):
        if not self.keepOpen:
            self.db.close()

    def getShows(self):
        shows = []
        try:
            db = self._open()
            cur = db.cursor()
            cur.execute("SELECT * from shows")
            rows = cur.fetchall()
            for r in rows:
                show = TVShow(*r)
                shows.append(show)
                cur.execute("SELECT number, id, airedDate, lastUpdated, season from tvdbepisodes WHERE show_fk = ? ", (show.tvdbid,))
                eps = cur.fetchall()
                if eps:
                    for e in eps:
                        e_dict = {'number':e[0], 'id':e[1], 'date':e[2], 'lastUpdated':e[3]}
                        s = e[4]
                        if not s in show.airedSeasons.keys():
                            show.airedSeasons[s] = []
                        show.airedSeasons[s].append(e_dict)
        finally:
            self._close()
        return shows

    def updateShow(self, show):
        try:
            db = self._open()
            cur = db.cursor()
            if show.id is None:
                cur.execute("INSERT INTO shows (name, path, filename, season, minepisode, enabled, tvdbid, enabled_override, notify_email) values (?,?,?,?,?,?,?,?,?)",
                  (show.name, show.path, show.filename, show.season, show.minepisode, show.enabled, show.tvdbid, show.enabled_override, show.notify_email))
            else:
                cur.execute("UPDATE shows SET name=?, path=?, filename=?, season=?, minepisode=?, enabled=?, tvdbid=?, enabled_override=? WHERE id=?",
                  (show.name, show.path, show.filename, show.season, show.minepisode, show.enabled, show.tvdbid, show.enabled_override, show.id))
            # Drop all current episode listings and update with latest data
            cur.execute("DELETE from tvdbepisodes where show_fk=?",(show.tvdbid,))
            for s in show.airedSeasons.keys():
                for e in show.airedSeasons[s]:
                    cur.execute("INSERT INTO tvdbepisodes (id, number, season, show_fk, lastUpdated, airedDate) values (?,?,?,?,?,?)",
                      (e['id'], e['number'], s, show.tvdbid, e['lastUpdated'], e['date']))
            db.commit()
        finally:
            self._close()

    def getShow(self, id):
        try:
            db = self._open()
            cur = db.cursor()
            cur.execute("SELECT * from shows WHERE id = ?", (id,))
            show = TVShow(*cur.fetchone())
            cur.execute("SELECT number, id, airedDate, lastUpdated, season from tvdbepisodes WHERE show_fk = ? ", (show.tvdbid,))
            eps = cur.fetchall()
            if eps:
                for e in eps:
                    e_dict = {'number':e[0], 'id':e[1], 'date':e[2], 'lastUpdated':e[3]}
                    s = e[4]
                    if not s in show.airedSeasons.keys():
                        show.airedSeasons[s] = []
                    show.airedSeasons[s].append(e_dict)
            return show
        finally:
            self._close()

    def removeShow(self, id):
        try:
            db = self._open()
            cur = db.cursor()
            cur.execute("SELECT tvdbid from shows WHERE id = ?",(id,))
            ret = cur.fetchone()
            if ret and ret[0]:
                cur.execute("DELETE from tvdbepisodes WHERE show_fk = ?", (ret[0],))
            cur.execute("DELETE from shows WHERE id = ?", (id,))
            db.commit()
        finally:
            self._close()

class MovieDB():
    def __init__(self, dbpath, keepOpen=False):
        self.dbpath = dbpath
        self.db = None
        self.keepOpen = keepOpen
        if keepOpen:
            self.db = sqlite3.connect(self.dbpath)

    def __delete__(self):
        if self.keepOpen:
            self.db.close()

    def _open(self):
        if not self.keepOpen:
            self.db = sqlite3.connect(self.dbpath)
        return self.db

    def _close(self):
        if not self.keepOpen:
            self.db.close()

    def addMovie(self, id, name, year, hashstr, email ):
        try:
            db = self._open()
            cur = db.cursor()
            cur.execute("INSERT INTO movies (id, name, year, tor_hash, notify_email) values (?,?,?,?,?)", (id,name, year, hashstr, email))
            db.commit()
        finally:
            self._close()

    def getMovies(self):
        movies = []
        try:
            db = self._open()
            cur = db.cursor()
            cur.execute("SELECT id, name, year, tor_hash, notify_email from movies")
            rows = cur.fetchall()
            for r in rows:
                movies.append({'id':r[0],'name':r[1],'year':r[2],'tor_hash':r[3], 'notify_email':r[4]})
        finally:
            self._close()
        return movies

    def getMovieWithHash(self, tor_hash):
        try:
            db = self._open()
            cur = db.cursor()
            cur.execute("SELECT id, name, year, tor_hash, notify_email from movies where tor_hash=?",(tor_hash,))
            res = cur.fetchone()
            if res:
                return {'id':res[0],'name':res[1],'year':res[2],'tor_hash':res[3], 'notify_email':res[4]}
            else:
                return None
        finally:
            self._close()

    def removeMovie(self, id):
        try:
            db = self._open()
            cur = db.cursor()
            cur.execute("DELETE from movies WHERE id = ?",(id,))
            db.commit()
        finally:
            self._close()
