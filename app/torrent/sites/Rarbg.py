from rarbgapi import RarbgAPI
from torrent.sites.BaseSearch import BaseSearch

class Search(BaseSearch):
    def __init__(self):
        self.api = RarbgAPI()

    def search(self, terms, settings={}):
        torrents = []
        raw_torrents = self.api.search(terms,format_='json_extended')
        if raw_torrents:
            for t in raw_torrents:
#                print(t.__dict__)
                torrents.append({'url':t.download,
                                 'name':t.filename,
                                 'seeds':t._raw['seeders'],
                                 'leechers':t._raw['leechers'],
                                })
        sorted_torrents = sorted(torrents,key = lambda k: k['seeds'], reverse=True)
        return sorted_torrents

if __name__ == '__main__':
    s = Search()
    results = s.search('deadliest catch')
    print(results)

