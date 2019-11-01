from flask import Flask, request, make_response, jsonify, render_template, redirect, url_for
from slurpee.utilities import settingsFromFile, settingsFromEnv, TVDBSearch, TMDBSearch
from slurpee.dataTypes import ShowDB, TVShow, MovieDB
from torrent.scrape import lookForTarget
import transmissionrpc
import os
from werkzeug.exceptions import BadRequest
from slurpee.parsing import hasEpisodeInDir

app = Flask(__name__)

flaskdebug = True if os.environ.get('FLASK_DEBUG', 0) else False

if flaskdebug:
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

settings_path = os.environ.get('SETTINGS_PATH',None)
if settings_path and os.path.exists(settings_path):
    settings = settingsFromFile(settings_path)
else:
    settings = settingsFromEnv()

@app.route('/')
@app.route('/index.html')
def root():
    shows = ShowDB(settings['SHOWS_DB_PATH'])
    return render_template('index.html', shows=shows.getShows())

@app.route('/list')
def showMissing():
    shows = ShowDB(settings['SHOWS_DB_PATH']).getShows()
    for show in shows:
        show.airedSeasons.pop(0,None)
        for s in show.airedSeasons.keys():
            for e in show.airedSeasons[s]:
                show_dir = os.path.join(show.path,"Season "+str(s))
                if hasEpisodeInDir(show_dir,int(s),int(e['number'])):
                    e['available'] = 1
                else:
                    e['available'] = 0
    return render_template('missing.html', shows=shows)

@app.route('/addnew')
def newShow():
    return render_template('addnew.html')

@app.route('/addmovie')
def newMovie():
    return render_template('addmovie.html')

@app.route('/shows', methods=['GET', 'POST'])
def listShows():
    if request.method == 'POST':
      print(request.form)
      basePath = settings['DEFAULT_BASE_PATH']
      show = TVShow(
               None,
               request.form.get('name'),
               os.path.join(basePath,'TV',request.form.get('name')),
               request.form.get('name').replace(' ','.'),
               request.form.get('season'),
               1,
               1,
               request.form.get('tvdbid'),
               0,
               request.form.get('notify_email')
             )
      if show.tvdbid:
          tvdb = TVDBSearch(settings['TVDB_API_KEY'],'en-us')
          show.airedSeasons = tvdb.getDetails(show.tvdbid)
         
      shows = ShowDB(settings['SHOWS_DB_PATH'])
      shows.updateShow(show)
      return redirect(url_for('root',status='success',action='add',asset=show.name))
    else:
      shows = ShowDB(settings['SHOWS_DB_PATH'])
      return make_response(jsonify(shows=[e.toDict() for e in shows.getShows() ]) , 200)

@app.route('/movies', methods=['POST'])
def postMovie():
    print(request.form)
    movie_name = request.form.get('name')
    movie_tmdbid = request.form.get('tmdbid')
    movie_year = request.form.get('release_date').split('-')[0]

    results = lookForTarget(settings, movie_name)
    # We only accept results that have the release year in them, to make sure we don't get oodles of porn.
    ret = []
    for torrent in results:
        if torrent['name'].find(movie_year) != -1:
            ret.append(torrent)
            if len(ret) >= 10:
                break
    return make_response(jsonify(ret), 200)


@app.route('/torrent', methods=['POST'])
def postTorrent():
    print(request.form)
    torrent_url = request.form.get('url')
    movie_name = request.form.get('name')
    movie_tmdbid = request.form.get('tmdbid')
    movie_year = request.form.get('release_date').split('-')[0]
    movie_email = request.form.get('notify_email')

    print(torrent_url)
    tc = transmissionrpc.Client(settings['RPC_HOST'], port=settings['RPC_PORT'], user=settings['RPC_USER'], password=settings['RPC_PASS'])
    t = tc.add_uri(torrent_url)
    tid = list(t)[0]
    print(tid)
    movies = MovieDB(settings['SHOWS_DB_PATH'])
    movies.addMovie(movie_tmdbid, movie_name, movie_year, t[tid].hashString, movie_email)
    return redirect(url_for('root', status='success', action='add',asset=movie_name))

@app.route('/shows/<int:id>', methods=['GET', 'POST', 'DELETE'])
def singleShow(id):
    shows = ShowDB(settings['SHOWS_DB_PATH'])
    show = shows.getShow(id)
    if request.method == 'GET':
        return make_response(jsonify(show.toDict()), 200)
    elif request.method == 'POST':
        if 'name' in request.form and len(request.form.get('name')) > 0:
            show.name = request.form.get('name')
        if 'path' in request.form and len(request.form.get('path')) > 0:
            show.path = request.form.get('path')
        if 'filename' in request.form and len(request.form.get('filename')) > 0:
            show.filename = request.form.get('filename')
        if 'season' in request.form and len(request.form.get('season')) > 0:
            show.season = int(request.form.get('season'))
        if 'minepisode' in request.form and len(request.form.get('minepisode')) > 0:
            show.minepisode = int(request.form.get('minepisode'))
        if 'enabled_override' in request.form:
            show.enabled_override = 1
        else:
            show.enabled_override = 0
        if 'notify_email' in request.form:
            email = request.form.get('notify_email')
            if email is not None:
                if shows.notify_email is None or len(shows.notify_email) == 0:
                    shows.notify_email = email
                elif email not in shows.notify_email.split(','):
                    shows.notify_email = ','.join(shows.notify_email,email)             
        shows.updateShow(show)
        return redirect(url_for('root',status='success',action='update',asset=show.name))
    elif request.method == 'DELETE':
        shows.removeShow(id)
        return (url_for('root',status='success',action='delete',asset=show.name), 200)

@app.route('/shows/search')
def tvdbSearch():
    if not 'name' in request.args:
        return BadRequest('name not provided')

    name = request.args.get('name')
    tvdb = TVDBSearch(settings['TVDB_API_KEY'],'en-us')
    return make_response(jsonify(tvdb.search(name)), 200)

@app.route('/movies/search')
def tmdbSearch():
    if not 'name' in request.args:
        return BadRequest('name not provided')

    name = request.args.get('name')
    tmdb = TMDBSearch(settings['THEMOVIEDB_API_KEY'])
    return make_response(jsonify(tmdb.search(name)),200)
    
if __name__ == "__main__":
    app.run()

