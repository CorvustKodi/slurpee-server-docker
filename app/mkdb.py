import xml.dom.minidom
import sqlite3, sys

with sqlite3.connect(sys.argv[1]) as conn:
  conn.execute('CREATE TABLE IF NOT EXISTS shows (id INTEGER PRIMARY KEY, name TEXT, path TEXT, filename TEXT, season INTEGER, minepisode INTEGER, enabled INTEGER)')
  print('Table created')
  conn.execute('CREATE TABLE IF NOT EXISTS movies (torrentid INTEGER PRIMARY KEY, name TEXT, path TEXT, themoviedbid INTEGER)')
  print('Table created')
  conn.commit()
