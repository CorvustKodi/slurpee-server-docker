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
import datetime

def lookForTarget(settings, targetName):
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
            results = engine.search(urllib.parse.quote(targetName),settings)
            sanitizedTarget = parsing.sanitizeString(targetName)
            if len(results) == 0 and sanitizedTarget != targetName:
                results = engine.search(urllib.parse.quote(sanitizedTarget),settings)
            if len(results) > 0:
                maxMatches = 10
                for res in results:
                    if maxMatches <= 0:
                        break
                    if parsing.fuzzyMatch(targetName,res) and res['seeds'] > 0:
                        bestResults.append(res)
                        maxMatches = maxMatches - 1
            else:
                print('No results returned.')
                continue
        except Exception as details:
            print('An error occured: %s' % details)
            traceback.print_exc()
    if len(bestResults) > 0:
        bestResults = sorted(bestResults,key = lambda k: k['seeds'], reverse=True)
    return bestResults

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
        if show.enabled and not show.enabled_override:
            print('Checking %s' % show.name)
            try:
              if show.tvdbid and show.airedSeasons:
                # This show has episode information, so we can go ahead and grab a bunch of episodes at once 
                # And we don't have to look for episodes that don't exist
                # show.season now becomes the minimum season we will search for
                dlPerShow = 10                
                for season in sorted(show.airedSeasons.keys()):
                    if dlPerShow <= 0:
                        break
                    if season < show.season:
                        continue
                    dir_path = os.path.join(show.path,'Season %d' % season)
                    if not os.path.exists(show.path):
                        makeChownDirs(show.path,settings['FILE_OWNER'])
                    if not os.path.exists(dir_path):
                        makeChownDirs(dir_path,settings['FILE_OWNER'])
                    for episode in sorted(show.airedSeasons[season], key = lambda k: k['number']):
                        if dlPerShow <= 0:
                            break
                        try:
                            e_date = datetime.datetime.strptime(episode['date'],"%Y-%m-%d").date()
                            td = e_date - datetime.date.today()
                            if td.days > -1:
                                # wait until the episdoe is airing, don't try to download it yet.
                                continue
                        except:
                            # If the date isn't defined, skip it, it's likely way off in the future
                            continue
                        if season < 10:
                            season_str = '0' + str(season)
                        else:
                            season_str = str(season)
                        if episode['number'] < 10:
                            episode_str = '0' + str(episode['number'])
                        else:
                            episode_str = str(episode['number'])
                        targetName = show.filename+'.s'+season_str+'e'+episode_str
                        if not parsing.hasEpisodeInDir(dir_path, int(season),int(episode['number'])):
                            bestResults = lookForTarget(settings,targetName)
                            if len(bestResults):
                                dlTorrent = bestResults[0]
                                found = False
                                for tfile in torrentFiles:
                                    hasMatch = parsing.fuzzyMatch(targetName,str(tfile))
                                    if hasMatch != None:
                                        print('Found existing download: %s' % tfile)
                                        found = True
                                        break
                                if not found:
                                    for t in activeTorrents:
                                        hasMatch = parsing.fuzzyMatch(targetName, str(t._get_name_string()))
                                        if hasMatch != None:
                                            print('Found existing torrent: %s' % t._get_name_string())
                                            found = True
                                            break
                                if not found:
                                    print('Adding torrent: %s' % dlTorrent['url'])
                                    tc.add_uri(dlTorrent['url'])
                                    dlPerShow = dlPerShow - 1
                                    break
              else:
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
                bestResults = lookForTarget(settings,targetName)
                if len(bestResults):
                    dlTorrent = bestResults[0]
                    found = False
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
