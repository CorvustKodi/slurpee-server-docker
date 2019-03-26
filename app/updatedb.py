import sys, os
from slurpee.utilities import settingsFromFile, settingsFromEnv, TVDBSearch
from slurpee.dataTypes import ShowDB
import datetime

def matchInDir(dir_path,filename):
    for f in os.listdir(dir_path):
        hasMatch = parsing.fuzzyMatch(filename,f)
        if hasMatch != None:
            return True
    return False


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
        missingEpisode = False
        for s in seasons.keys():
            if missingEpisode:
                break
            # Ignore season 0, it's specials
            if int(s) <= 0:
                continue
            for e in seasons[s]:
                show_dir = os.path.join(show.path,"Season %d" % int(s))
                if not os.path.exists(show_dir) or not matchInDir( show_dir,show.filename + '.s'+ str(s) +'e' + str(e['number']) ):
                    missingEpisode = True
                    break
                edate = datetime.datetime.strptime(e['date'],"%Y-%m-%d").date()
                if not lastAiredDate or lastAiredDate < edate:
                    lastAiredDate = edate
        if not missingEpisode and datetime.date.today() > lastAiredDate:
            show.enabled = False
        else:
            show.enabled = True
        allshows.updateShow(show)
        print(show)
    exit(0)


