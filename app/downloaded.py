#!/usr/bin/python

import sys
import os
import traceback
import time
import transmissionrpc

import slurpee.parsing as parsing
from slurpee.dataTypes import ShowDB, MovieDB
from slurpee.utilities import sendMail, settingsFromFile, settingsFromEnv, makeChownDirs, safeCopy
from slurpee.parsing import getExtension

video_extensions = ['mp4', 'mov', 'mkv', 'avi', 'mpg', 'm4v']
audio_extensions = ['mp3']


def processFiles(files, settings):
    ''' 
      Process a lits of files and copy them to appropriate locations      
    '''
    try:
        allshows = ShowDB(settings['SHOWS_DB_PATH']).getShows()

        download_path = settings['DOWNLOADS_PATH']

        default_video_output_path = os.path.join(settings['DEFAULT_NEW_PATH'],"Video")
        default_audio_output_path = os.path.join(settings['DEFAULT_NEW_PATH'],"Audio")
        if not os.path.exists(default_video_output_path):
            makeChownDirs(default_video_output_path,settings['FILE_OWNER'])
        if not os.path.exists(default_audio_output_path):
            makeChownDirs(default_audio_output_path,settings['FILE_OWNER'])

        video_files = []
        audio_files = []

        for file_name in files:
            file_ext = getExtension(file_name)
            if file_ext in video_extensions and file_name not in video_files:
                video_files.append(file_name)
            if file_ext in audio_extensions and file_name not in audio_files:
                audio_files.append(file_name)

        for tfile in audio_files:
            try:
                # No fancy processing for audio files, just copy to the NEW directory
                safeCopy(
                    os.path.join(download_path,tfile), 
                    os.path.join(default_audio_output_path,os.path.basename(tfile)),
                    settings['FILE_OWNER']
                )
            except:
                pass

        for tfile in video_files:
            matches = []
            foundShow = False
            for show in allshows:
                if show.enabled:
                    print('Checking %s' % show.name)
                    if parsing.fuzzyMatch(show.filename,str(tfile)) != None:
                        matches.append(show)
                        foundShow = True
            if not foundShow:
                print('No match found for vidoe file %s' % tfile)
                try:
                    print('Copying to default video directory: %s' % os.path.join(download_path,os.path.basename(tfile)))
                    safeCopy(
                        os.path.join(os.path.join(download_path,tfile), 
                        os.path.join(default_video_output_path,os.path.basename(tfile)),
                        settings['FILE_OWNER']
                    )
                    if settings['MAIL_ENABLED']:
                        sendMail(settings,'New video downloaded','%s - new file in videos' % os.path.basename(tfile))
                except:
                    pass
            else:
                # All of the shows in 'matching' appear in the video filename. It stands to reason
                # that the longest show name will be the best (kinda true right?)
                bestmatch = matches[0]
                for show in matches:
                    if len(show.filename) > len(bestmatch.filename):
                        bestmatch = show

                season, episode = parsing.parseEpisode(os.path.basename(tfile))
                if int(season) < 10:
                    season = '0' + str(int(season))
                if int(episode) < 10:
                    episode = '0' + str(int(episode))

                print("best match is %s" % bestmatch.name)
                dest_dir = os.path.join(bestmatch.path,'Season %d' % int(season))
                if not os.path.exists(dest_dir):
                    makeChownDirs(dest_dir,settings['FILE_OWNER'])

                if os.path.exists(dest_dir):
                    target_file = bestmatch.filename + ' s' + str(season) + 'e' + str(episode) + '.' + parsing.getExtension(str(tfile))
                    if not os.path.isfile(os.path.join(dest_dir,target_file)):
                        print("Copying from %s to %s" % (os.path.join(download_path,tfile),os.path.join(dest_dir, target_file)))
                        safeCopy(
                            os.path.join(os.path.join(download_path,tfile), 
                            os.path.join(dest_dir,target_file),
                            settings['FILE_OWNER']
                        )

                        if settings['MAIL_ENABLED']:
                            sendMail(settings,'%s - new episode available' % bestmatch.name,'A new episode of %s is available for playback in \
                              %s/Season %d: %s' % (bestmatch.name, bestmatch.path, int(season),target_file))
                    else:
                        print("Target file %s already exists" % os.path.join(dest_dir,target_file))
    except Exception:
        exc_details = traceback.format_exc()
        print('%s' % exc_details)
        if settings['MAIL_ENABLED']:
            sendMail(settings,'An error has occurred',exc_details)

def mover(settings, tid = None):
    ''' The mover function is called by transmission when download is complete.
      It is responsible for extracting the proper video files from the set
      of files downloaded by the torrent, and placing them in the correct
      destination directory.
    '''
    try:
        if tid == None:
            tid = os.environ.get('TR_TORRENT_ID')
        torrent_id = None
        if tid is not None:
           torrent_id = int(tid)
           print('Torrent ID: %d' % torrent_id)

        tc = transmissionrpc.Client(settings['RPC_HOST'], port=settings['RPC_PORT'], user=settings['RPC_USER'], password=settings['RPC_PASS'])
        files_dict = tc.get_files()
        torrent_list = tc.get_torrents()
        
        if torrent_id != None:
            t = tc.get_torrent(torrent_id)
        movie = None
        mdb = MovieDB(settings['SHOWS_DB_PATH'])
        if t:
            movie = mdb.getMovieWithHash(t.hashString)
        if movie:
            for k in files_dict[torrent_id].keys():
                file_name = files_dict[torrent_id][k]['name']
                file_ext = getExtension(file_name)
                if file_ext in video_extensions and parsing.fuzzyMatch(movie['name'],os.path.basename(file_name)) != None and file_name.find('sample') == -1:
                    print("Found a file for %s: %s" % (movie['name'],file_name))
                    dest_dir = os.path.join(settings['DEFAULT_BASE_PATH'],'Movies')
                    safeCopy(
                        os.path.join(os.path.join(settings['DOWNLOADS_PATH'],file_name),
                        os.path.join(dest_dir,os.path.basename(file_name)),
                        settings['FILE_OWNER']
                    )
                    if settings['MAIL_ENABLED']:
                        sendMail(settings,'%s downloaded' % movie['name'],'%s has been downloaded to %s' % (movie['name'], os.path.join(dest_dir,os.path.basename(file_name))))
            mdb.removeMovie(movie['id'])
        else:
            files_list = []
            if torrent_id != None and torrent_id in files_dict.keys():
                for k in files_dict[torrent_id].keys():
                    files_list.append(files_dict[torrent_id][k]['name'])
            else:
                print('No ID match, processing all torrents')
                for t in files_dict.keys():
                    for k in files_dict[t].keys():
                        files_list.append(files_dict[t][k]['name'])
            print(files_list)
            processFiles(files_list, settings)
    except Exception:
        exc_details = traceback.format_exc()
        print('%s' % exc_details)
        if settings['MAIL_ENABLED']:
            sendMail(settings,'An error has occurred',exc_details)

def cleanup(settings):
    try:
        tc = transmissionrpc.Client(settings['RPC_HOST'], port=settings['RPC_PORT'], user=settings['RPC_USER'], password=settings['RPC_PASS'])
        torrent_list = tc.get_torrents()
        now = time.time()
        oneDay = 60*60*24
        oneWeek = oneDay*7
        for t in torrent_list:
            doneDate = t.__getattr__('doneDate')
            id = int(t.__getattr__('id'))
            if doneDate > 0 and doneDate < (now - oneWeek):
                print('Found an old torrent (id = %d) - removing.' % id)
                tc.remove_torrent(id,True)
            elif doneDate > 0 and doneDate < (now - oneDay):
                # Clean up torrents that don't have useful files after 24 hours
                hasGoodFile = False
                for f in t.files().values():
                    file_ext = getExtension(f['name'])
                    if file_ext in video_extensions or file_ext in audio_extensions:
                        hasGoodFile = True
                        break
                if not hasGoodFile:
                    print('Found a useless torrent (id = %d) - removing.' % id)
                    tc.remove_torrent(id,True)
                    
    except Exception:
        exc_details = traceback.format_exc()
        print('%s' % exc_details)
        if settings['MAIL_ENABLED']:
            sendMail(settings,'An error has occurred',exc_details)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        settings = settingsFromFile(sys.argv[1])
    else:
        settings = settingsFromEnv()
    for f in os.listdir('/done-torrents'):
        try:
            mover(settings,int(os.path.basename(f)))
        finally:
            os.remove(os.path.join('/done-torrents',f))
    cleanup(settings)
