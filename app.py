#!/usr/bin/python

import sys
sys.path += ['lib']
import os
import time
import ConfigParser
import flask
import requests
import utils
import math
import MySQLdb
import MySQLdb.cursors
from thread import start_new_thread as daemonize
from pprint import pprint


# Attempt to read the configuration file
cfg = ConfigParser.ConfigParser()
try:
    cfg.read('main.cfg')
except Exception as e:
    print("There was an issue parsing main.cfg (%s)" % str(e))
    print("Please fix these issues then restart paste.ml!")
    os._exit(1)

app = flask.Flask(__name__)
prefix = cfg.get('Database', 'db-prefix').rstrip('_')


def db_connect():
    return MySQLdb.connect(
        host=str(cfg.get('Database', 'db-hostname')),
        port=int(cfg.get('Database', 'db-port')),
        user=str(cfg.get('Database', 'db-user')),
        passwd=str(cfg.get('Database', 'db-password')),
        db=cfg.get('Database', 'db-name'),
        cursorclass=MySQLdb.cursors.DictCursor)


def query(*args):
    db = db_connect()

    c = db.cursor()
    c.execute(*args)
    return list(c.fetchall())


def write(*args):
    db = db_connect()

    c = db.cursor()
    try:
        c.execute(*args)
        db.commit()
    except:
        try:
            db.rollback()
        except:
            pass
    return list(c.fetchall())


def bg_write(*args):
    """ Run a query in the background if it's not runtime dependant """
    return daemonize(write, tuple(args))


def uuid():
    reserved = ['login', 'logout', 'signin', 'signout', 'about', 'index', 'api']
    while True:
        _tmp = utils.gen_word(2, 3)
        if _tmp in reserved:
            continue
        if not query("""SELECT id FROM {}_content WHERE id = %s""".format(prefix), [_tmp]):
            return _tmp

@app.route('/')
def main():
    return flask.render_template('new.html', paste=False)


@app.route('/dup/<paste>')
@app.route('/dup/<paste>.<lang>')
def duplicate(paste, lang=None):
    if not utils.validate(paste):
        return flask.redirect('/')
    return flask.render_template('new.html', dup=paste)


@app.route('/api/pastes', methods=['POST'])
@app.route('/api/pastes/<int:page>', methods=['POST'])
@utils.auth
def api_user(page=1):
    limit = 8  # Assuming they want 8 results per page
    if page < 1:
        _page = 1
    _page = int(page) -1
    _page = _page * limit
    data = {}
    try:
        data['posts'] = query("""SELECT id, language, language_short, created, last_modified, hits FROM {}_content WHERE author = %s ORDER BY last_modified DESC LIMIT %s,%s""".format(prefix), [flask.session['git']['id'], _page, limit])
        for i in range(len(data['posts'])):
            data['posts'][i]['hrt'] = utils.hrt(int(data['posts'][i]['last_modified']))
            if data['posts'][i]['language_short']:
                data['posts'][i]['language_short'] = '.' + data['posts'][i]['language_short']
        data['count'] = query("""SELECT COUNT(id) AS cnt FROM {}_content WHERE author = %s""".format(prefix), [flask.session['git']['id']])[0]['cnt']
        data['pages'] = int(math.ceil(float(data['count']) / float(8)))
        data['page_current'] = int(page)
        if data['page_current'] >= 3:
            data['page_range'] = range(int(page) - 2, range(data['pages'], data['pages'] + 2)[:2][-1])
        else:
            data['page_range'] = range(1, data['pages'] + 1)[:5]
        data['success'] = True
        return flask.jsonify(data)
    except Exception as e:
        print repr(str(e))
        data['success'] = False
        return flask.jsonify(data)


@app.route('/api/stats', methods=['POST'])
def api_stats():
    data = {}
    limit = 5
    try:
        _lang = query("""SELECT language, COUNT(language) AS ct FROM {}_content WHERE author = %s GROUP BY language ORDER BY ct DESC""".format(prefix), [flask.session['git']['id']])
        for i in range(len(_lang)):
            if _lang[i]['ct'] < 1:
                _lang[i]['ct'] = 1
        if len(_lang) > 5:
            cnt = 0
            data['languages'] = _lang[:5] + [{
                'ct': sum([i['ct'] for i in _lang[5:]]),
                'language': 'other'
            }]
            data['languages'] = sorted(data['languages'], key=lambda k: k['ct'], reverse=True) 
        else:
            data['languages'] = _lang
        data['success'] = True
        return flask.jsonify(data)
    except Exception as e:
        print repr(str(e))
        data['success'] = False
        return flask.jsonify(data)


@app.route('/api/submit', methods=['POST'])
def api_submit():
    form = flask.request.form
    req = ['paste', 'language', 'short']
    for item in req:
        if item not in form:
            return flask.jsonify({
                'success': False,
                'message': 'Invalid submission data.'
            })

    # Too short.. anything below 5 characters is really small and is likely bullshit
    if len(form['paste']) < 5:
        return flask.jsonify({
            'success': False,
            'message': 'Paste is too short!'
        })

    # Too long. It's set to 70,000 characters as this is both degrading to the end
    # user, as well as the server. Anything above this is getting to be rediculous.
    if len(form['paste']) > 70000:
        return flask.jsonify({
            'success': False,
            'message': 'Paste is too long!'
        })

    # Theoretically at this point there shouldn't be any other errors, maybe in
    # the future, check to see if a user is in a blacklisted set of IP's/users?

    id = uuid()
    author = int(flask.session['git']['id']) if 'authed' in flask.session else None
    language = form['language'] if form['language'] else None
    language_short = form['short'] if form['short'] else None
    created = int(time.time())
    last_view = created
    last_modified = created
    ip = flask.request.remote_addr
    hits = 1
    if language_short:
        uri = "%s.%s" % (id, language_short)
    elif language:
        uri = "%s.%s" % (id, language)
    else:
        uri = id
    write("""INSERT INTO {}_content VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""".format(prefix), (
        id, form['paste'], author, language, language_short, created, last_view, last_modified, ip, hits))

    return flask.jsonify({
        'success': True,
        'message': 'Created paste',
        'uri': uri,
    })


@app.route('/<paste>')
def pull_paste(paste):
    if not utils.validate(paste):
        return flask.redirect('/')
    return flask.render_template('paste.html', paste=paste.lower())


@app.route('/api/<paste>')
@app.route('/api/<paste>.<lang>')
def api(paste, lang=None):
    if not utils.validate(paste):
        return flask.redirect('/')
    if paste.lower() == 'about' and str(lang).lower() == 'md':
        try:
            with open('README.md', 'r') as f:
                file = f.read()
                data = {
                    'paste': file,
                    'lines': len(file.split('\n')),
                    'chars': len(file),
                    'language': 'markdown'
                }
                return flask.jsonify(data)
        except:
            pass
    _tmp = query("""SELECT * FROM {}_content WHERE id = %s""".format(prefix), [paste.lower()])
    if len(_tmp) > 1 or len(_tmp) < 1:
        return flask.redirect('/')

    bg_write("""UPDATE {}_content SET last_view = %s WHERE id = %s""".format(prefix), [int(time.time()), paste.lower()])
    bg_write("""UPDATE {}_content SET hits = hits + 1 WHERE id = %s""".format(prefix), [paste.lower()])
    if not lang:
        lang = _tmp[0]['language']
    else:
        lang = lang.lower()
    data = {
        'paste': _tmp[0]['content'],
        'lines': len(_tmp[0]['content'].split('\n')),
        'chars': len(_tmp[0]['content']),
        'language': lang
    }
    return flask.jsonify(data)


@app.route('/t/<paste>')
@app.route('/t/<paste>.<lang>')
def plaintext(paste, lang=None):
    if not utils.validate(paste):
        return flask.redirect('/')
    if paste.lower() == 'about' and str(lang).lower() == 'md':
        try:
            with open('README.md', 'r') as f:
                return flask.Response(f.read(), mimetype='text/plain')
        except:
            pass
    _tmp = query("""SELECT * FROM {}_content WHERE id = %s""".format(prefix), [paste.lower()])
    if len(_tmp) > 1 or len(_tmp) < 1:
        return flask.redirect('/')
    bg_write("""UPDATE {}_content SET last_view = %s WHERE id = %s""".format(prefix), [int(time.time()), paste.lower()])
    bg_write("""UPDATE {}_content SET hits = hits + 1 WHERE id = %s""".format(prefix), [paste.lower()])
    return flask.Response(_tmp[0]['content'], mimetype='text/plain')


@app.route('/login')
def process_login():
    if 'authed' in flask.session:
        if flask.session['authed']:
            return flask.redirect('/')
    errors, warnings, msgs = [], [], []
    args = flask.request.args
    err = args.get('error')

    # Support using next for anything inter-website
    if args.get('next'):
        flask.session['next'] = args.get('next')

    if err:
        # More info: http://git.io/veeEM
        # We've got to figure out what specifically is the issue, then depending
        # on what it is, send the end user a response as a heads-up
        if err == 'application_suspended':
            errors.append('An internal error occurred. Please contact <a href="mailto:%s">%s</a> if the issue persists.' % (
                cfg.get('Contact-info', 'email'), cfg.get('Contact-info', 'name')
            ))
        elif err == 'redirect_uri_mismatch':
            errors.append('An internal error occurred. Please contact <a href="mailto:%s">%s</a> if the issue persists.' % (
                cfg.get('Contact-info', 'email'), cfg.get('Contact-info', 'name')
            ))
        elif err == 'access_denied':
            msgs.append(
                'To be able to use this service, you will need to login to Github and validate paste.ml.<br><br>'
                '<a href="/login" class="btn btn-md btn-success">Please try again <i class="fa fa-chevron-right"></i></a>'
            )
        else:
            errors.append('An unknown response from Github was received. Unable to authenticate you.')
    elif args.get('code'):
        # "If the user accepts your request, GitHub redirects back to your site
        # with a temporary code in a code parameter as well as the state you
        # provided in the previous step in a state parameter. If the states don't
        # match, the request has been created by a third party and the process
        # should be aborted."
        if args.get('state') == flask.session['state']:
            # Actually do the stuff here, as we've confirmed it's a response
            # from Github.

            # This is what we need to get the oauth token, to pull api data
            flask.session['code'] = args['code']

            uri = 'https://github.com/login/oauth/access_token'
            headers = {
                'Accept': 'application/json'
            }
            payload = {
                'client_id': cfg.get('Github', 'client-id'),
                'client_secret': cfg.get('Github', 'client-secret'),
                'code': flask.session['code']
            }
            try:
                data = requests.post(uri, headers=headers, data=payload, timeout=10).json()
                # pprint(data)
                if 'error' in data:
                    if data['error'] == 'incorrect_client_credentials':
                        errors.append('An internal error occurred. Please contact <a href="mailto:%s">%s</a> if the issue persists.' % (
                            cfg.get('Contact-info', 'email'), cfg.get('Contact-info', 'name')
                        ))
                    elif data['error'] == 'redirect_uri_mismatch':
                        errors.append('An internal error occurred. Please contact <a href="mailto:%s">%s</a> if the issue persists.' % (
                            cfg.get('Contact-info', 'email'), cfg.get('Contact-info', 'name')
                        ))
                    elif data['error'] == 'bad_verification_code':
                        msgs.append(
                            'It seems when attempting to login you in, your session has expired.<br><br>'
                            '<a href="/login" class="btn btn-md btn-success">Please try again <i class="fa fa-chevron-right"></i></a>'
                        )
                    else:
                        errors.append('An unknown response from Github was received. Unable to authenticate you.')
                else:
                    flask.session['token'] = data['access_token']
                    # Now, we should be good to make API calls
                    # In the future, store the last etag from the last call
                    # just in case, because then we can:
                    #   * Prevent rate-limiting more
                    #   * Allow quicker API checks to finish the login process
                    uri = 'https://api.github.com/user'
                    headers = {
                        'Authorization': 'token %s' % flask.session['token'],
                        # Per Githubs request, we're adding a user-agent just
                        # in case they need to get ahold of us.
                        'User-Agent': 'https://github.com/Liamraystanley/dropbin.git'
                    }
                    api_call = requests.get(uri, headers=headers).json()
                    pprint(api_call)
                    flask.session['git'] = api_call
                    flask.session['authed'] = True
            except:
                errors.append('There was an error authenticating with Github. Please try again.')
        else:
            # The state GET attribute either exists and doesn't match, or doesn't
            # exist. Either way, it's not legitimate.
            errors.append('Invalid information returned from Github. Was the authentication spoofed?')
    else:
        # We need to start constructing the authorization URL here.
        uri = 'https://github.com/login/oauth/authorize?client_id={id}&state={rand}'
        flask.session['state'] = utils.gen_rand(10)
        return flask.redirect(uri.format(id=cfg.get('Github', 'client-id'), rand=flask.session['state']))

    if errors or warnings or msgs:
        return flask.render_template('messages.html', errors=errors, warnings=warnings, msgs=msgs)
    else:
        # Support using next for anything inter-website
        if 'next' in flask.session:
            return flask.redirect('/%s' % flask.session['next'])
        return flask.redirect('/')  # Eventually we'll redirect to a controlpanel?


@app.route('/logout')
def process_logout():
    if 'authed' in flask.session:
        flask.session.clear()

    # Support using next for anything inter-website
    if flask.request.args.get('next'):
        return flask.redirect('/%s' % flask.request.args.get('next'))
    return flask.redirect('/')


@app.context_processor
def utility_processor():
    def commas(number):
        return "{:,d}".format(number)

    return dict(
        commas=commas
    )


@app.errorhandler(404)
def page_not_found(error):
    """ Catch all for any outdated pastes, or anything of that sort """
    return flask.redirect('/')


# @app.after_request
# def add_header(response):
#     """
#         Add headers to both force latest IE rendering engine or Chrome Frame,
#         and also to cache the rendered page for 10 minutes.
#     """
#     response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
#     response.headers['Cache-Control'] = 'public, max-age=600'
#     return response


def main():
    app.secret_key = cfg.get('General', 'salt')
    # Do some initial stuff with tables to ensure everythings been added:
    query("""CREATE TABLE IF NOT EXISTS {}_content (
        id VARCHAR(50) NOT NULL,
        content MEDIUMTEXT,
        author INTEGER,
        language VARCHAR(50),
        language_short VARCHAR(50),
        created INTEGER NOT NULL,
        last_view INTEGER NOT NULL,
        last_modified INTEGER NOT NULL,
        ip VARCHAR(255) NOT NULL,
        PRIMARY KEY (id)
    )""".format(prefix))

    query("""CREATE TABLE IF NOT EXISTS {}_users (
        uid INTEGER NOT NULL,
        login VARCHAR(255) NOT NULL,
        name VARCHAR(255),
        avatar VARCHAR(255),
        location VARCHAR(255),
        email VARCHAR(255),
        created INTEGER NOT NULL,
        last_login INTEGER NOT NULL,
        admin BOOLEAN,
        PRIMARY KEY (uid)
    )""".format(prefix))


main()

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=80, threaded=True)
