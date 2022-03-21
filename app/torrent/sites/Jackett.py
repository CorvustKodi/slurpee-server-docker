import traceback
import urllib
import requests
import json
from torrent.sites.BaseSearch import BaseSearch


class Search(BaseSearch):
    def __init__(self):
        pass

    def search(self, terms, settings):
        torrents = []
        print("Searching for \"%s\"" % terms)
        try:
            url = "%s/api/v2.0/indexers/%s/results?apikey=%s&Query=%s" % (
                settings.get("JACKETT_URL"),
                settings.get("JACKETT_INDEXER"),
                settings.get("JACKETT_API_KEY"),
                urllib.parse.quote(terms) 
            )
            r = requests.get(url)
            if r.status_code != 200:
                print("The request to Jackettt failed: (%s)" % r.status_code)
                print("For %s" % url)
                return torrents

            results = json.loads(r.content)['Results']
            for r in results:
                torrent_url = r['MagnetUri'] if r['MagnetUri'] else r['Link']
                if torrent_url.startswith(settings.get("JACKETT_URL")):

                    redirect_response = requests.get(torrent_url, allow_redirects=False)
                    if redirect_response.status_code == 302:
                        torrent_url = redirect_response.headers["Location"]

                torrents.append({
                    'url': torrent_url,
                    'name': r['Title'],
                    'seeds': r['Seeders'],
                    'leachers': 0
                })
            torrents = sorted(torrents,key = lambda k: k['seeds'], reverse=True)
        except Exception as e:
            print("The request to Jackett failed.")
            traceback.print_exc()

        return torrents
