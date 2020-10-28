import re,sys
import socket
import requests
from torrent.sites.BaseSearch import BaseSearch
from bs4 import BeautifulSoup, BeautifulStoneSoup, Tag

socket.setdefaulttimeout(15)

def getLink(url):
    f = None
    try:
        r = requests.get(url,headers={'Accept-encoding':'gzip'})
        f = r.text
        soup = BeautifulSoup(f,features="html.parser")
        # Look for a Cloudfare redirect ? 
        formNodes = soup.findAll('form', {'id' : 'challenge-form'})
        if formNodes:
          urlpath = formNodes[0]['action']
          params = ''
          first = True
          for child in soup.findAll('input', {'type' : 'hidden'}):
            iname = child['name']
            ivalue = None
            try:
              ivalue = child['value']
            except:
              pass
            if ivalue is None:
              ivalue = "wtf"
            if not first:
              params = params + '&'
            params = params + iname + '=' + ivalue
            first = False
          newUrl = url + urlpath + '?' + params
          print('redirect to: %s' % newUrl)
          r = requests.get(newUrl,headers={'Accept-encoding':'gzip'})
          f = r.text
    except:
        pass
    return f

class Search(BaseSearch):
    def __init__(self):
        self.search_uris = ['https://limetorrents.cc/search/all/'
                           ]
    def search(self, terms, settings={}):
        torrents = []
        f = None

        for url in self.search_uris:
            final_url = url + terms.replace(' ','%20') + '/seeds/1/'
            print( 'search URL: %s' % final_url)
            f = getLink(final_url)
            if f is not None:
                break;
        if not f:
            raise Exception('Out of proxies')
        soup = BeautifulSoup(f,features="html.parser")
        links = []
        for details in soup.findAll('div', {'class': 'tt-name'}):
            sub = details.findAll('a');
            for a in sub:
                if a['href'].find('.torrent?') == -1:
                    par = details.parent.parent
                    seedNode = None
                    leechNode = None
                    for sib in par.next_siblings:
                        if isinstance(sib,Tag) and 'class' in sib.attrs.keys():
                            if not seedNode and 'tdseed' in sib['class']:
                                seedNode = sib
                            if not leechNode and 'tdleech' in sib['class']:
                                leechNode = sib
                        if seedNode and leechNode:
                            break
                    if seedNode is None or leechNode is None:
                        break;

                    name = a.text

                    seeds = int(seedNode.text.replace(',',''))
                    leechers = int(leechNode.text.replace(',',''))            
                    trusted = False
                    if par.find('img', {'title':'Verified torrent'}) is not None:
                        trusted = True


                    turl = a['href']
                    # Follow the new link
                    baseUrl = final_url.split('/')[0:3]
                    turl = '/'.join(baseUrl) + turl
                    f = getLink(turl)
                    if not f:
                        raise Exception('Invalid link')
                    newSoup = BeautifulSoup(f,features="html.parser")
                    for mag in newSoup.findAll('a'):
                        if mag['href'].startswith('magnet:?'):
                            url = mag['href']
                    if trusted or 'trusted_uploaders' not in settings.keys() or str(settings['trusted_uploaders']).lower() != 'true':
                        torrents.append({
                                 'url': url,
                                 'name': name,
                                 'seeds': seeds,
                                 'leechers': leechers,
                        })
        sorted_torrents = sorted(torrents,key = lambda k: k['seeds'], reverse=True)
        return sorted_torrents

if __name__ == '__main__':
    s = Search()
    results = s.search('deadliest catch')
    print(results)

