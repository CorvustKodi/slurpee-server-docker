import xml.dom.minidom
import sqlite3, sys

with sqlite3.connect(sys.argv[1]) as conn:
  conn.execute('CREATE TABLE IF NOT EXISTS shows (id INTEGER PRIMARY KEY, name TEXT, path TEXT, filename TEXT, season INTEGER, minepisode INTEGER, enabled INTEGER)')
  conn.execute('CREATE TABLE IF NOT EXISTS movies (torrentid INTEGER PRIMARY KEY, name TEXT, path TEXT, themoviedbid INTEGER)')
  conn.execute('CREATE TABLE IF NOT EXISTS tvdbepisodes (id INTEGER, number INTEGER, season INTEGER, show_fk INTEGER, lastUpdated INTEGER, airedDate TEXT)')
  try:
    conn.execute('ALTER TABLE shows ADD COLUMN tvdbid INTEGER')
  except:
    pass

  conn.commit()
  print('Database created/updated')
