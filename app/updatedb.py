import sys
from slurpee.utilities import settingsFromFile, settingsFromEnv, TVDBSearch
from slurpee.dataTypes import ShowDB

if __name__ == '__main__':
    if len(sys.argv) > 1:
        settings = settingsFromFile(sys.argv[1])
    else:
        settings = settingsFromEnv()
    allshows = ShowDB(settings['SHOWS_DB_PATH'])
    for show in allshows.getShows():
        if not show.tvdbid:
            continue
        tvdb = TVDBSearch(settings['TVDB_API_KEY'],'en-us')
        seasons = tvdb.getDetails(show.tvdbid)
        show.airedSeasons = seasons
        allshows.updateShow(show)
    exit(0)


