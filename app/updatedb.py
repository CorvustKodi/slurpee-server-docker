import sys
from slurpee.utilities import settingsFromFile, settingsFromEnv, TVDBSearch
from slurpee.dataTypes import ShowDB
from datetime import date

if __name__ == '__main__':
    if len(sys.argv) > 1:
        settings = settingsFromFile(sys.argv[1])
    else:
        settings = settingsFromEnv()
    allshows = ShowDB(settings['SHOWS_DB_PATH'])
    lastAiredDate = None
    for show in allshows.getShows():
        if not show.tvdbid:
            continue
        tvdb = TVDBSearch(settings['TVDB_API_KEY'],'en-us')
        seasons = tvdb.getDetails(show.tvdbid)
        show.airedSeasons = seasons
        for s in seasons.keys():
            for e in seasons[s]:
                if not lastAiredDate or lastAiredDate < date.fromisoformat(e['date']):
                    lastAiredDate = date.fromisoformat(e['date'])
        date.today() > lastAiredDate:
            show.enabled = False
        else:
            show.enabled = True
        allshows.updateShow(show)
    exit(0)


