from slurpee.dataTypes import ShowDB
import sys

db = ShowDB(sys.argv[1])
print(db.getShows())

