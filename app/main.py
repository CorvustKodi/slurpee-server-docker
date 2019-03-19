from flask import Flask, request, make_response, jsonify, render_template, redirect, url_for
from slurpee.utilities import settingsFromFile, settingsFromEnv, TVDBSearch
from slurpee.dataTypes import ShowDB, TVShow
import os
from werkzeug.exceptions import BadRequest

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

@app.route('/addnew')
def newShow():
    return render_template('addnew.html')

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
               1
             )
      shows = ShowDB(settings['SHOWS_DB_PATH'])
      shows.updateShow(show)
      return redirect(url_for('root',status='success',action='add',asset=show.name))
    else:
      shows = ShowDB(settings['SHOWS_DB_PATH'])
      return make_response(jsonify(shows=[e.toDict() for e in shows.getShows() ]) , 200)

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
        if 'enabled' in request.form:
            show.enabled = 1
        else:
            show.enabled = 0
        shows.updateShow(show)
        return redirect(url_for('root',status='success',action='update',asset=show.name))
    elif request.method == 'DELETE':
        shows.removeShow(id)
        return (url_for('root',status='success',action='delete',asset=show.name), 200)

@app.route('/torrent/<int:id>')
def torrentDone(id):
    print('Call to /torrent/'+str(id))
    open('/done-torrents/'+str(id),'x')
    return make_response('{"success":1}', 200)

@app.route('/shows/search')
def tvdbSearch():
    if not 'name' in request.args:
        return BadRequest('name not provided')

    name = request.args.get('name')
    tvdb = TVDBSearch(settings['TVDB_API_KEY'],'en-us')
    return make_response(jsonify(tvdb.search(name)), 200)
    
if __name__ == "__main__":
    app.run()

