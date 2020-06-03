import sys, os
from slurpee.utilities import settingsFromFile, settingsFromEnv, TMDBSearch
from slurpee.dataTypes import ShowDB
from slurpee.parsing import hasEpisodeInDir

import datetime

if __name__ == '__main__':
    if len(sys.argv) > 1:
        settings = settingsFromFile(sys.argv[1])
    else:
        settings = settingsFromEnv()
    allshows = ShowDB(settings['SHOWS_DB_PATH'])
    for show in allshows.getShows():
        lastAiredDate = None
        tvdb = TMDBSearch(settings['THEMOVIEDB_API_KEY'],'en-us', 'tv')
        if not show.tvdbid:
            # Do a lookup against theTVDB. Add the ID ONLY if we get an exact name match, which we should since Plex
            # pretty much requires the folder names to match theTVDB names.
            searchResults = tvdb.search(show.name)
            for r in searchResults:
                if r['name'].lower() == show.name.lower():
                    show.tvdbid = int(r['id'])
                    break
        if not show.tvdbid:
            print("Could not find a TVDB id for " + show.name)
            continue
        seasons = tvdb.getTVDetails(show.tvdbid)
        show.airedSeasons = seasons
        missingEpisode = False
        for s in seasons.keys():
            if missingEpisode:
                break
            # Ignore season 0, it's specials
            if int(s) < show.season:
                continue
            for e in seasons[s]:
                try:
                    edate = datetime.datetime.strptime(e['date'],"%Y-%m-%d").date()
                    if not lastAiredDate or lastAiredDate < edate:
                        lastAiredDate = edate
                except Exception:
                    # Some episodes won't have a date defined if the next season has been confirmed, but no air date is set.
                    pass
                show_dir = os.path.join(show.path,"Season %d" % int(s))
                if not os.path.exists(show_dir) or not hasEpisodeInDir(show_dir,int(s), int(e['number']) ):
                    if e['date']:
                        missingEpisode = True
                        print("Found missing episode s%de%d for %s,air date: %s" % (int(s),int(e['number']),show.name,e['date']))
                        break
        # If there is a missing episode that has already aired, enable the show
        if missingEpisode and lastAiredDate and lastAiredDate < datetime.date.today():
            show.enabled = True
        else:
            show.enabled = False
        allshows.updateShow(show)
    exit(0)


