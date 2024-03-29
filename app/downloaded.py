#!/usr/bin/python

import sys
import os
import traceback
import time
import transmissionrpc
from datetime import datetime, timedelta

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
    allshows = ShowDB(settings['SHOWS_DB_PATH']).getShows()

    download_path = settings['DOWNLOADS_PATH']
    incomplete_path = settings['INCOMPLETE_PATH']

    default_video_output_path = os.path.join(settings['DEFAULT_NEW_PATH'],"Video")
    default_audio_output_path = os.path.join(settings['DEFAULT_NEW_PATH'],"Audio")
    if not os.path.exists(default_video_output_path):
        makeChownDirs(default_video_output_path,settings['FILE_OWNER'])
    if not os.path.exists(default_audio_output_path):
        makeChownDirs(default_audio_output_path,settings['FILE_OWNER'])

    video_files = []
    audio_files = []

    for f in files:
        file_ext = getExtension(f['name'])
        if file_ext in video_extensions and f['name'] not in [vf['name'] for vf in video_files] and f['selected']:
            video_files.append(f)
        if file_ext in audio_extensions and f['name'] not in [af['name'] for af in audio_files] and f['selected']:
            audio_files.append(f)

    for tfile in audio_files:
        # No fancy processing for audio files, just copy to the NEW directory
        safeCopy(
            os.path.join(download_path,tfile['name']),
            os.path.join(default_audio_output_path,os.path.basename(tfile['name'])),
            settings['FILE_OWNER'],
            backup_src=os.path.join(os.path.join(incomplete_path,tfile['name'])),
            file_size=tfile['completed'] if tfile['selected'] else 0
        )

    for tfile in video_files:
        matches = []
        foundShow = False
        for show in allshows:
            if show.enabled:
                print('Checking %s' % show.name)
                if parsing.fuzzyMatch(show.filename,str(tfile['name'])) != None:
                    matches.append(show)
                    foundShow = True
        if not foundShow:
            print('No match found for vidoe file %s' % tfile['name'])
            print('Copying to default video directory: %s' % os.path.join(download_path,os.path.basename(tfile['name'])))
            if safeCopy(
                os.path.join(os.path.join(download_path,tfile['name'])),
                os.path.join(default_video_output_path,os.path.basename(tfile['name'])),
                settings['FILE_OWNER'],
                backup_src=os.path.join(os.path.join(incomplete_path,tfile['name'])),
                file_size=tfile['completed'] if tfile['selected'] else 0
            ) and settings['MAIL_ENABLED']:
                sendMail(settings,'New video downloaded','%s - new file in videos' % os.path.basename(tfile['name']))
        else:
            # All of the shows in 'matching' appear in the video filename. It stands to reason
            # that the longest show name will be the best (kinda true right?)
            bestmatch = matches[0]
            for show in matches:
                if len(show.filename) > len(bestmatch.filename):
                    bestmatch = show

            season, episode = parsing.parseEpisode(os.path.basename(tfile['name']))
            if int(season) < 10:
                season = '0' + str(int(season))
            if int(episode) < 10:
                episode = '0' + str(int(episode))

            print("best match is %s" % bestmatch.name)
            dest_dir = os.path.join(bestmatch.path,'Season %d' % int(season))
            if not os.path.exists(dest_dir):
                makeChownDirs(dest_dir,settings['FILE_OWNER'])

            if os.path.exists(dest_dir):
                target_file = bestmatch.filename + ' s' + str(season) + 'e' + str(episode) + '.' + parsing.getExtension(str(tfile['name']))
                if not os.path.isfile(os.path.join(dest_dir,target_file)):
                    print("Copying from %s to %s" % (os.path.join(download_path,tfile['name']),os.path.join(dest_dir, target_file)))
                    if safeCopy(
                        os.path.join(os.path.join(download_path,tfile['name'])),
                        os.path.join(dest_dir,target_file),
                        settings['FILE_OWNER'],
                        backup_src=os.path.join(os.path.join(incomplete_path,tfile['name'])),
                        file_size=tfile['completed'] if tfile['selected'] else 0
                    ) and settings['MAIL_ENABLED']:
                        sendMail(settings,'%s - new episode available' % bestmatch.name,'A new episode of %s is available for playback in \
                          %s/Season %d: %s' % (bestmatch.name, bestmatch.path, int(season),target_file))
                        if show.notify_email is not None and len(show.notify_email) > 0:
                            for email in show.notify_email.split(','):
                                sendMail(settings,'%s - new episode available' % bestmatch.name,'A new episode of %s is available: %s' % (bestmatch.name, target_file), dest=email)

                else:
                    print("Target file %s already exists" % os.path.join(dest_dir,target_file))

def mover(settings, thash = None):
    ''' The mover function is called by transmission when download is complete.
      It is responsible for extracting the proper video files from the set
      of files downloaded by the torrent, and placing them in the correct
      destination directory.
    '''
    if thash == None:
        thash = os.environ.get('TR_TORRENT_HASH')

    tc = transmissionrpc.Client(settings['RPC_HOST'], port=settings['RPC_PORT'], user=settings['RPC_USER'], password=settings['RPC_PASS'])
    files_dict = tc.get_files()
    torrent_list = tc.get_torrents()
    t = None
    for torrent in torrent_list:
        if torrent.hashString == thash:
            t = torrent
            break
    if t is None:
        print("Could not find torrent with hash %s" % thash)
        if settings['MAIL_ENABLED']:
            sendMail(settings,'An error has occurred','Could not find torrent with hash %s' % thash)
        return

    movie = None
    mdb = MovieDB(settings['SHOWS_DB_PATH'])
    movie = mdb.getMovieWithHash(t.hashString)
    if movie:
        for k in files_dict[t.id].keys():
            file_name = files_dict[t.id][k]['name']
            file_ext = getExtension(file_name)
            if file_ext in video_extensions and parsing.fuzzyMatch(movie['name'],os.path.basename(file_name)) != None and file_name.find('sample') == -1:
                print("Found a file for %s: %s" % (movie['name'],file_name))
                dest_dir = os.path.join(settings['DEFAULT_BASE_PATH'],'Movies')
                if safeCopy(
                    os.path.join(os.path.join(settings['DOWNLOADS_PATH'],file_name)),
                    os.path.join(dest_dir,os.path.basename(file_name)),
                    settings['FILE_OWNER']
                ) and settings['MAIL_ENABLED']:
                    sendMail(settings,'%s downloaded' % movie['name'],'%s has been downloaded to %s' % (movie['name'], os.path.join(dest_dir,os.path.basename(file_name))))
                    if movie['notify_email'] is not None and len(movie['notify_email']) > 0:
                        for email in movie['notify_email'].split(','):
                            sendMail(settings,'%s downloaded' % movie['name'],'%s has been downloaded ' % (movie['name']),dest=email)

        mdb.removeMovie(movie['id'])
    else:
        files_list = []
        if t.id in files_dict.keys():
            files_list = files_dict[t.id].values()
        else:
            print('No ID match, processing all torrents')
            for t in files_dict.keys():
                files_list.extend(files_dict[t].values())
        processFiles(files_list, settings)

def cleanup(settings):
    try:
        tc = transmissionrpc.Client(settings['RPC_HOST'], port=settings['RPC_PORT'], user=settings['RPC_USER'], password=settings['RPC_PASS'])
        torrent_list = tc.get_torrents()
        now = time.time()
        for t in torrent_list:
            doneDate = t.date_done
            startDate = t.date_started
            id = int(t.__getattr__('id'))
            if startDate > datetime.fromtimestamp(0) and startDate < (datetime.fromtimestamp(now) - timedelta(weeks=1)):
                print('Found an old torrent (id = %d) - removing.' % id)
                tc.remove_torrent(id, True)
            elif doneDate > datetime.fromtimestamp(0) and doneDate < (datetime.fromtimestamp(now) - timedelta(days=3)):
                print('Found a completed torrent (id = %d) - removing.' % id)
                tc.remove_torrent(id, True)
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
            mover(settings,os.path.basename(f))
            os.remove(os.path.join('/done-torrents',f))
        except Exception:
            exc_details = traceback.format_exc()
            print('%s' % exc_details)
            if settings['MAIL_ENABLED']:
                sendMail(settings,'An error has occurred',exc_details)
    cleanup(settings)
