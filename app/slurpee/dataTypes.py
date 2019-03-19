import xml.dom.minidom
import sqlite3

class TVShow():
    def __init__(self, id, name, path, filename, season, minepisode, enabled):
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
          'enabled':self.enabled
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
                shows.append(TVShow(*r))
        finally:
            self._close()
        return shows

    def updateShow(self, show):
        try:
            db = self._open()
            cur = db.cursor()
            if show.id is None:
                cur.execute("INSERT INTO shows (name, path, filename, season, minepisode, enabled) values (?,?,?,?,?,?)",
                  (show.name, show.path, show.filename, show.season, show.minepisode, show.enabled))
            else:
                cur.execute("UPDATE shows SET path=?, filename=?, season=?, minepisode=?, enabled=? WHERE id=?",
                  (show.path, show.filename, show.season, show.minepisode, show.enabled, show.id))
            db.commit()
        finally:
            self._close()

    def getShow(self, id):
        try:
            db = self._open()
            cur = db.cursor()
            cur.execute("SELECT * from shows WHERE id = ?", (id,))
            return TVShow(*cur.fetchone())
        finally:
            self._close()

    def removeShow(self, id):
        try:
            db = self._open()
            cur = db.cursor()
            cur.execute("DELETE from shows WHERE id = ?", (id,))
            db.commit()
        finally:
            self._close()
