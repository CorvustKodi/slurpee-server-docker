import requests,urllib
import json
import os,shutil
import time
from xml.dom.minidom import parse
import smtplib
from email.message import EmailMessage
import traceback
from copy import deepcopy

baseSettings = {'RPC_HOST':'127.0.0.1', 'RPC_PORT':2580, 'RPC_USER':'', 
    'RPC_PASS':'', 'TRUSTEDONLY':False, 'SEARCHERS':[], 'SHOWS_DB_PATH':'',
    'MAIL_ENABLED':False, 'MAIL_DEST':'', 'SMTP_HOST':'', 'SMTP_PORT':25,
    'SMTP_SECURE':False, 'SMTP_USER':'', 'SMTP_PASS':'', 'DEFAULT_NEW_PATH':'',
    'DEFAULT_BASE_PATH':'', 'DOWNLOADS_PATH':'', 'FILE_OWNER':'', 'TVDB_API_KEY':'',
    'THEMOVIEDB_API_KEY':''
}

def settingsFromEnv():
    ret = deepcopy(baseSettings)
    ret['RPC_HOST'] = os.environ.get('RPC_HOST',ret['RPC_HOST'])
    ret['RPC_PORT'] = int(os.environ.get('RPC_PORT',ret['RPC_PORT']))
    ret['RPC_USER'] = os.environ.get('RPC_USER',ret['RPC_USER'])
    ret['RPC_PASS'] = os.environ.get('RPC_PASS',ret['RPC_PASS'])
    t = os.environ.get('TRUSTEDONLY',None)
    if t in ['true', 'True', 'TRUE', 't', 'T', '1']:
        ret['TRUSTEDONLY'] = True
    else:
        ret['TRUSTEDONLY'] = False
    s = os.environ.get('SEARCHERS',None)
    if s:
        ret['SEARCHERS'] = s.split(',')
    ret['SHOWS_DB_PATH'] = os.environ.get('SHOWS_DB_PATH',ret['SHOWS_DB_PATH'])
    t = os.environ.get('MAIL_ENABLED',None)
    if t in ['true', 'True', 'TRUE', 't', 'T', '1']:
        ret['MAIL_ENABLED'] = True
    else:
        ret['MAIL_ENABLED'] = False
    ret['MAIL_DEST'] = os.environ.get('MAIL_DEST',ret['MAIL_DEST'])
    ret['SMTP_HOST'] = os.environ.get('SMTP_HOST',ret['SMTP_HOST'])
    ret['SMTP_PORT'] = int(os.environ.get('SMTP_PORT',ret['SMTP_PORT']))
    t = os.environ.get('SMTP_SECURE',None)
    if t in ['true', 'True', 'TRUE', 't', 'T', '1']:
        ret['SMTP_SECURE'] = True
    else:
        ret['SMTP_SECURE'] = False
    ret['SMTP_USER'] = os.environ.get('SMTP_USER',ret['SMTP_USER'])
    ret['SMTP_PASS'] = os.environ.get('SMTP_PASS',ret['SMTP_PASS'])
    ret['DEFAULT_NEW_PATH'] = os.environ.get('DEFAULT_NEW_PATH',ret['DEFAULT_NEW_PATH'])
    ret['DEFAULT_BASE_PATH'] = os.environ.get('DEFAULT_BASE_PATH',ret['DEFAULT_BASE_PATH'])
    ret['DOWNLOADS_PATH'] = os.environ.get('DOWNLOADS_PATH',ret['DOWNLOADS_PATH'])
    ret['FILE_OWNER'] = os.environ.get('FILE_OWNER',ret['FILE_OWNER'])
    ret['TVDB_API_KEY'] = os.environ.get('TVDB_API_KEY',ret['TVDB_API_KEY'])
    ret['THEMOVIEDB_API_KEY'] = os.environ.get('THEMOVIEDB_API_KEY',ret['THEMOVIEDB_API_KEY'])
    return ret

def settingsFromFile(settings_file):
    ret = deepcopy(baseSettings)
    try:
        doc2 = parse(settings_file)
        settingsNodes = doc2.getElementsByTagName('setting')
        for node in settingsNodes:
            if node.attributes['id'].value == 'rpc_host':
                ret['RPC_HOST'] = node.attributes['value'].value
            if node.attributes['id'].value == 'rpc_port':
                ret['RPC_PORT'] = node.attributes['value'].value
            if node.attributes['id'].value == 'rpc_user':
                ret['RPC_USER'] = node.attributes['value'].value
            if node.attributes['id'].value == 'rpc_pass':
                ret['RPC_PASS'] = node.attributes['value'].value

            if node.attributes['id'].value == 'search_trustedonly':
                if str(node.attributes['value'].value).lower() == 'true':
                    ret['TRUSTEDONLY'] = True
            if node.attributes['id'].value == 'search_enable_limetorrents':
                if str(node.attributes['value'].value).lower() == 'true':
                    ret['SEARCHERS'].append('LimeTorrents')
            if node.attributes['id'].value == 'search_enable_tpb':
                if str(node.attributes['value'].value).lower() == 'true':
                    ret['SEARCHERS'].append('ThePirateBay')

            if node.attributes['id'].value =='shows_db_path':
                ret['SHOWS_DB_PATH'] = node.attributes['value'].value
            if node.attributes['id'].value =='default_new_path':
                ret['DEFAULT_NEW_PATH'] = node.attributes['value'].value
            if node.attributes['id'].value =='default_base_path':
                ret['DEFAULT_BASE_PATH'] = node.attributes['value'].value
            if node.attributes['id'].value =='downloads_path':
                ret['DOWNLOADS_PATH'] = node.attributes['value'].value
            if node.attributes['id'].value =='file_owner':
                ret['FILE_OWNER'] = node.attributes['value'].value

            if node.attributes['id'].value == 'mail_enabled':
                if str(node.attributes['value'].value).lower() == 'true':
                    ret['MAIL_ENABLED'] = True
            if node.attributes['id'].value == 'smtp_secure':
                if str(node.attributes['value'].value).lower() == 'true':
                    ret['SMTP_SECURE'] = True
            if node.attributes['id'].value == 'mail_dest':
                ret['MAIL_DEST'] = node.attributes['value'].value
            if node.attributes['id'].value == 'smtp_host':
                ret['SMTP_HOST'] = node.attributes['value'].value
            if node.attributes['id'].value == 'smtp_port':
                ret['SMTP_PORT'] = node.attributes['value'].value
            if node.attributes['id'].value == 'smtp_user':
                ret['SMTP_USER'] = node.attributes['value'].value
            if node.attributes['id'].value == 'smtp_pass':
                ret['SMTP_PASS'] = node.attributes['value'].value

            if node.attributes['id'].value == 'tvdb_api_key':
                ret['TVDB_API_KEY'] = node.attributes['value'].value
            if node.attributes['id'].value == 'themoviedb_api_key':
                ret['THEMOVIEDB_API_KEY'] = node.attributes['value'].value

    except:
        pass
    return ret

def sendMail(settings,subject_text,body_text):
  try:
    if settings['SMTP_SECURE']:
        server = smtplib.SMTP_SSL(settings['SMTP_HOST'], settings['SMTP_PORT'])
    else:
        server = smtplib.SMTP(settings['SMTP_HOST'], settings['SMTP_PORT'])
    server.login(settings['SMTP_USER'],settings['SMTP_PASS'])

    msg = EmailMessage()
    msg.set_content(body_text)
    msg['Subject'] = subject_text
    msg['From'] = "Slurpee"
    msg['To'] = settings['MAIL_DEST']

    server.send_message(msg)
    server.quit()
  except:
    exc_details = traceback.format_exc()
    print('%s' % exc_details)

def doChown(path, owner):
   toks = owner.split(':')
   shutil.chown(path,toks[0],toks[1])

def makeChownDirs(path, owner):
    if not path or os.path.exists(path):
        return []
    (head, tail) = os.path.split(path)
    res = makeChownDirs(head, owner)
    os.mkdir(path)
    doChown(path, owner)
    res += [path]
    return res

def safeCopy(source, dest, owner, retry=True):
    orig_size = os.path.getsize(source)
    shutil.copy(source, dest)
    doChown(dest,owner)
    dest_size = os.path.getsize(dest)
    if orig_size != dest_size:
        os.unlink(dest)
        if retry:
            time.sleep(10)
            safeCopy(source,dest,owner,retry=False)
        else:
            raise Exception('Failed to copy to %s - invalid destination size' % dest)
            
    
class TVDBSearch(object):
    
    def login(self):
        resp = requests.post(self.tvdbApi+'/login',json={'apikey':self.apiKey})
        if not resp.ok:
            print('Failed to authenticate to TVDB: '+str(resp.status_code))
            resp.raise_for_status()
        respJ = resp.json()
        self.jwtToken = respJ['token']
    
    def __init__(self, apiKey, language):
        self.lang = language
        self.tvdbApi = 'https://api.thetvdb.com'
        self.apiKey = apiKey
        self.jwtToken = None
        self.login()
        
    def search(self, showTitle):
        
        search_url = self.tvdbApi + "/search/series?name=" + urllib.parse.quote(showTitle)
        if self.jwtToken is None:
            self.login()
        if self.jwtToken is None:
            print('Could not authenticate!')
            return None
        
        headers = {'Authorization' : 'Bearer ' + self.jwtToken, \
                   'Accept-Language' : self.lang, \
                   'Accept' : 'application/json'}
        tvdb = requests.get(search_url,headers=headers)
        respJ = tvdb.json()
        if 'data' not in respJ.keys():
            return []
        seriesNodes = respJ['data']
        for node in seriesNodes:
           node['seriesName'] = node['seriesName'].replace('(','').replace(')','')
        return seriesNodes

    def getDetails(self, showID):
        seasons = {}        
        search_url = self.tvdbApi + "/series/" + str(showID) + "/episodes/summary"
        if self.jwtToken is None:
            self.login()
        if self.jwtToken is None:
            print('Could not authenticate!')
            return seasons
   
        headers = {'Authorization' : 'Bearer ' + self.jwtToken, \
                   'Accept-Language' : self.lang, \
                   'Accept' : 'application/json'}
        tvdb = requests.get(search_url,headers=headers)
        respJ = tvdb.json()
        if 'data' not in respJ.keys() or 'airedSeasons' not in respJ['data'].keys():
            return seasons
        for season in respJ['data']['airedSeasons']:
            seasonNumber = int(season)
            seasons[seasonNumber] = []
            search_url = self.tvdbApi + "/series/" + str(showID) + "/episodes/query?airedSeason=" + season
            tvdb = requests.get(search_url,headers=headers)
            seasonJ = tvdb.json()
            # Check for paging of the results
            if 'links' not in seasonJ.keys():
                continue
            curPage = int(seasonJ['links']['first'])
            lastPage = int(seasonJ['links']['last'])
            while curPage <= lastPage:
                curPage = curPage + 1
                if 'data' not in seasonJ.keys():
                    continue
                for episode in seasonJ['data']:
                    num = episode['airedEpisodeNumber']
                    date = episode['firstAired']
                    id = episode['id']
                    lastUpdated = episode['lastUpdated']
                    seasons[seasonNumber].append({'number':num , 'id':id, 'date':date, 'lastUpdated':lastUpdated})
                if curPage <= lastPage:
                    search_url = self.tvdbApi + "/series/" + str(showID) + "/episodes/query?airedSeason="+season+"&page="+str(curPage)
                    tvdb = requests.get(search_url,headers=headers)
                    seasonJ = tvdb.json()
        return seasons
        
class TMDBSearch(object):
    
    def search(self,title):
        request_url = self.baseURL + '/search/movie/' + '?api_key=' + self.apiKey + '&language=' + self.lang \
            + '&include_adult=false&page=1' + '&query=' + urllib.parse.quote(title)

        resp = requests.get(request_url)
        if not resp.ok:
            print('Failed request to TheMovieDB: '+str(resp.status_code))
            resp.raise_for_status()
        respJ = resp.json()
        results = []
        if 'results' in respJ.keys():
            results = respJ['results']
        # Useful keys in results: 'title', 'release_date', 'overview', 'poster_path'
        return results
    
    def __init__(self, apiKey, language='en-US'):
        self.lang = language
        self.baseURL = 'https://api.themoviedb.org/3'
        self.apiKey = apiKey
        self.basePosterPath='http://image.tmdb.org/t/p/w185'
 
