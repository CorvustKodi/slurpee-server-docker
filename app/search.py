import sys
from torrent.scrape import scraper
from slurpee.utilities import settingsFromFile, settingsFromEnv
from slurpee.dataTypes import ShowDB

if __name__ == '__main__':
    if len(sys.argv) > 1:
        settings = settingsFromFile(sys.argv[1])
    else:
        settings = settingsFromEnv()
    allshows = ShowDB(settings['SHOWS_DB_PATH'])
    scraper(settings,allshows)
    exit(0)


