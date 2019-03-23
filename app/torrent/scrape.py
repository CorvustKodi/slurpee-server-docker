#!/usr/bin/python

import os 
import urllib 
import transmissionrpc 
import time 
import socket 
import slurpee.parsing as parsing 
from slurpee.dataTypes import ShowDB
from slurpee.utilities import makeChownDirs
import sys                                                                        
import traceback
import importlib

def scraper(settings, allshows):
    socket.setdefaulttimeout(15)
    # Create the client connection to transmission
    tc = transmissionrpc.Client(settings['RPC_HOST'], port=settings['RPC_PORT'], user=settings['RPC_USER'], password=settings['RPC_PASS'])
    activeTorrents = tc.list().values()
    torrentFiles = []
    for torrent in activeTorrents:
        files_dict = tc.get_files(torrent.id)
        for id_key in files_dict.keys():
            for file_key in files_dict[id_key].keys():
                torrentFiles.append(files_dict[id_key][file_key]['name'].lower())
    for show in allshows.getShows():
        if show.enabled:
            print('Checking %s' % show.name)
            try:
                dlTorrent = None
                # Figure out what the next episode we need is - only download 1 episode per sweep.
                dir_path = os.path.join(show.path,'Season %d' % show.season)
                if not os.path.exists(show.path):
                    makeChownDirs(show.path,settings['FILE_OWNER'])
                if not os.path.exists(dir_path):
                    makeChownDirs(dir_path,settings['FILE_OWNER'])
                print('Directory path: %s' % dir_path)
                lastEpisode = show.minepisode-1
                for f in os.listdir(dir_path): 
                    hasMatch = parsing.fuzzyMatch(show.filename,f)
                    if hasMatch != None:
                        season, episode = parsing.parseEpisode(f);
                        print('%s = season %d, episode %d' % (f, season,episode))
                        if episode > lastEpisode:
                            lastEpisode = episode
                    else:
                        print("No fuzzy match between '%s' and '%s'" % (show.filename, f))
                nextEpisode = lastEpisode + 1
  
                if show.season < 10:
                    season_str = '0' + str(show.season)
                else:
                    season_str = str(show.season)
                if nextEpisode < 10:
                    episode_str = '0' + str(nextEpisode)
                else:
                    episode_str = str(nextEpisode)

                targetName = show.filename + '.s'+season_str+'e'+episode_str
                print('Looking for %s' % targetName)

                engine = None
                bestResults = []
                for SEARCHER in settings['SEARCHERS']:
                    try:
                        module_name = 'torrent.sites.'+SEARCHER
                        module = importlib.import_module(module_name)
                        class_ = getattr(module, 'Search')
                        print('Calling engine %s' % SEARCHER)
                        engine = class_()
                        results = engine.search(urllib.parse.quote(targetName),{'trusted_uploaders':settings['TRUSTEDONLY']})
                        sanitizedTarget = parsing.sanitizeString(targetName)
                        if len(results) == 0 and sanitizedTarget != targetName:
                            results = engine.search(urllib.parse.quote(sanitizedTarget),{'trusted_uploaders':settings['TRUSTEDONLY']})
                        if len(results) > 0:
                            for res in results:
                                if parsing.fuzzyMatch(targetName,res):
                                    dlTorrent = res
                                    break;
                        else:
                            print('No results returned.')
                            continue
                        found = False
                        if dlTorrent is not None :
                            bestResults.append(dlTorrent)
                    except Exception as details:
                        print('An error occured: %s' % details)
                        traceback.print_exc()
                if len(bestResults) > 0:
                    bestResults = sorted(bestResults,key = lambda k: k['seeds'], reverse=True)
                for dlTorrent in bestResults:
                    for tfile in torrentFiles:
                        hasMatch = parsing.fuzzyMatch(targetName,str(tfile))
                        if hasMatch != None:
                            print('Found existing download: %s' % tfile)
                            found = True
                            break
                    if not found:
                        print('Adding torrent: %s' % dlTorrent['url'])
                        tc.add_uri(dlTorrent['url'])
                        break
            except Exception as details:
                print('An error occured: %s' % details)
                traceback.print_exc()
            time.sleep(10)

def scrape(settings):
    allshows = dataTypes.ShowDB(settings['SHOWS_DB_PATH'])
    scraper(settings,allshows)

if __name__ == '__main__':
    settings = settingsFromFile(sys.argv[1])
    scrape(settings)
    exit(0)
