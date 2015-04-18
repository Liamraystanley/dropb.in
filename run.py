#!/usr/bin/python

import sys
sys.path += ['lib']
import os
import ConfigParser
import flask
import requests
import utils
from pprint import pprint


cfg = ConfigParser.ConfigParser()
app = flask.Flask(__name__)


example = """$(function() {
    // $('pre code').each(function(i, block) {
    //     hljs.highlightBlock(block);
    // });
    $('#text-input').focus();
    $('[data-toggle="tooltip"]').tooltip({
        container: 'body',
        placement: 'left'
    });
});


/*--------------------------------------------/
/ Possibly something to use in the future, to /
/ make it so when using the textarea, it will /
/ show line #'s. Breaks atm because layout.   /
/--------------------------------------------*/
// $(function(){
//     $('#text-input').bind('input propertychange', function() {
//         var n_lines = $('#text-input').val().split('\\n').length + 1;
//         var lines_data = '';
//         console.log(n_lines);
//         for (var i = 1; i < n_lines; i++) {
//             //$("#lines").append('<div>' + i + '.</div>');
//             var lines_data = lines_data.concat('<div>' + i + '.</div>');
//         };
//         console.log(lines_data);
//         $("#lines-edit").html(lines_data);
//     });
// });

function fetch(id) {
    $.ajax("/api/" + id, {
        type: "get",
        dataType: "json",
        success: function(data) {
            s = hljs.highlightAuto(data.paste);
            $("#box").html(s.value);
            // Add line numbers here
            for (var i = 0; i < data.lines; i++) {
                $("#lines").append('<a href="#' + (i + 1) + '"><div id="' + (i + 1) + '">' + (i + 1) + '.</div></a>');
            }
            $("#more-info").append("<span>" + s.language + "</span>");
            $("#more-info").append("<span>" + Number(data.lines).toLocaleString('en') + " lines</span>");
            $("#more-info").append("<span>" + Number(data.chars).toLocaleString('en') + " chars</span>");

            // As pre doesn't like to disable line wrapping, we're going to have to support it, due to the way the template is setup.
            // As such.. the best method is to split up the paste, find which lines are longer than the parent div, and append a <br>
            // to the line number id'd div. Slightly degrades performance on larger pastes.

            // Need to implement multiple-line splitting! Currently only works with ONE line!
            var id = 1;
            $($('#box').text().split('\\n')).each(function(index, value) {
                id += 1;
                var measure = document.createElement("span");
                measure.innerText = value;
                measure.style.display = 'none';
                $('#box')[0].appendChild(measure);
                var linewidth = $(measure).width();
                if (linewidth >= $("#box").width()) {
                    $("#" + (id - 1)).html((id - 1) + '.' + '<br><br>');
                }
                // console.log(index + ": " + $(this).text());
            });
        },
        error: function(e) {
            // later send a notification of failure...
        }
    });
}
"""


@app.route('/')
def main():
    return flask.render_template('new.html', paste=False)


@app.route('/<paste>')
def pull_paste(paste):
    return flask.render_template('paste.html', paste="herp")


@app.route('/api/<paste>')
def raw(paste):
    tmp = example.strip('\n')
    data = {
        'paste': tmp.strip('\n'),
        'lines': len(tmp.split('\n')),
        'chars': len(tmp)
    }
    return flask.jsonify(data)


@app.route('/t/<paste>')
def plaintext(paste):
    return flask.Response(example.strip('\n'), mimetype='text/plain')


@app.route('/login')
def process_login():
    if 'authed' in flask.session:
        if flask.session['authed']:
            return flask.redirect('/')
    errors, warnings, msgs = [], [], []
    args = flask.request.args
    err = args.get('error')

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
                        'User-Agent': 'https://github.com/Liamraystanley/paste.ml.git'
                    }
                    api_call = requests.get(uri, headers=headers).json()
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
        return flask.redirect('/')  # temp


@app.route('/logout')
def process_logout():
    if 'authed' in flask.session:
        flask.session.clear()
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


if __name__ == '__main__':
    try:
        cfg.read('main.cfg')
    except Exception as e:
        print("There was an issue parsing main.cfg (%s)" % str(e))
        print("Please fix these issues then restart paste.ml!")
        os._exit(1)
    app.secret_key = cfg.get('General', 'salt')
    app.debug = False
    app.run(host='0.0.0.0', port=80)
