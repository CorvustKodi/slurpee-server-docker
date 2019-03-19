import re
import socket
import requests
from torrent.sites.BaseSearch import BaseSearch
from bs4 import BeautifulSoup, BeautifulStoneSoup

socket.setdefaulttimeout(15)

class Search(BaseSearch):
    def __init__(self):
        self.search_uris = ['https://thepiratebay.rocks/search/'
                            ,'https://thepiratebay.org/search/'
                            ,'https://thepiratebay.se/search/'
                           ]
    def search(self, terms, settings={}):
        torrents = []
        f = None

        for url in self.search_uris:
            try:
                final_url = url + terms.replace(' ','%20')
                print('search URL: %s' % final_url)
                r = requests.get(final_url,headers={'Accept-encoding':'gzip'})
                f = r.text
                soup = BeautifulSoup(f,features="html.parser")
                # Look for a Cloudfare redirect ? 
                formNode = soup.findAll('form', {'id' : 'challenge-form'})[0]
                if formNode is not None:
                  urlpath = formNode['action']
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
                  soup = BeautifulSoup(f,features="html.parser")
                break
            except:
                pass
        if not f:
            raise Exception('Out of pirate bay proxies')
        soup = BeautifulSoup(f,features="html.parser")
        for details in soup.findAll('a', {'class': 'detLink'}):
            name = details.text
            url = details.findNext('a', {'href': re.compile('^magnet:')})['href']
            uploader = details.findNext('a', {'href' : re.compile('^/user/')})

            trusted = False
            try:
                for child in uploader.contents:
                    if child.name == u'img':
                        uploader_status = child['title']
                        if uploader_status.lower() == 'vip' or uploader_status.lower() == 'trusted':
                            trusted=True
            except:
                pass
            td = details.findNext('td')
            seeds = int(td.text)
            td = td.findNext('td')
            leechers = int(td.text)
            print( "name : %s, seeds: %d, trusted: %s" % (name,seeds,trusted))

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
