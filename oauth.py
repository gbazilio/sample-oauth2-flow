import os
import uuid
import flask
import requests
import json

from flask import Flask
from flask import render_template

app = Flask(__name__)

API_RESOURCE_URI = 'https://www.googleapis.com/drive/v2/files'
SCOPE = 'https://www.googleapis.com/auth/drive.readonly'

# both comes from Google API Console
#  after you have registered your applications
CLIENT_ID = os.environ['OAUTH_CLIENT_ID']
CLIENT_SECRET = os.environ['OAUTH_CLIENT_SECRET']

# url to redirect the user after authorization succeded or denied
REDIRECT_URI = 'http://localhost:5000/oauth2callback'

# Authorization endpoint
API_AUTHORIZATION_ENDPOINT = (
    'https://accounts.google.com/o/oauth2/auth?' +
    'response_type=code' + # requesting an Authorization Code Grant type
    '&client_id={}' + 
    '&redirect_uri={}' + 
    '&scope={}' +

    # access_type=offline means you're requesting offline access to this resource.
    #  Actually, this will add a Refresh Token to the response.
    #  It's also helpful to know that refresh tokens are generated ONLY ONCE.
    '&access_type=offline').format(
    CLIENT_ID, 
    REDIRECT_URI, 
    SCOPE)

API_ACCESS_TOKEN_ENDPOINT = 'https://www.googleapis.com/oauth2/v3/token'

@app.route('/')
def index():

    if 'credentials' not in flask.session :
        return render_template('home.html')
    else:
        # code runs only if user has authorized the application
        credentials = json.loads(flask.session['credentials'])
        
        # if we get here, it means what we all want: the Access Token
        #  so it is used to build the request to the private resource we want
        headers = {'Authorization': 'Bearer {}'.format(credentials['access_token'])}
        response = requests.get(API_RESOURCE_URI, headers=headers)

        if response.status_code != 200:
            return render_template('home.html')   

        return render_template('loggedin.html', results=response.text, token=flask.session['credentials'])

# function triggered when user's click the login button
@app.route('/login')
def login():

	# credentials variable is manually created in session
    if 'credentials' not in flask.session:

		# code, while in response, is the authorization code sent from the api authorization server
		#  which in this case is the google api.
        # if it is not part of the response, means the user has not allowed the app to access its resource yet
        if 'code' not in flask.request.args:
            return flask.redirect(API_AUTHORIZATION_ENDPOINT)

        else:

            return flask.redirect(flask.url_for())

# function triggered automatically after user is redirected back to the application
#  it exchanges the authorization code by an access token
@app.route('/oauth2callback')
def oauth2callback():

    # gets the authorization code sent by the api authorization server
    authorization_code = flask.request.args.get('code')

    data = {'code': authorization_code,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            '&scope': '',
            'grant_type': 'authorization_code'} # grant type says which flow of oauth we want to use

    # sends a request to exchange code by access token to the api authorization server
    response = requests.post(API_ACCESS_TOKEN_ENDPOINT, data=data)
    
    flask.session['credentials'] = response.text
    return flask.redirect(flask.url_for('index'))

@app.route('/logout')
def logout():
    del flask.session['credentials']
    return flask.redirect(flask.url_for('index'))

# this function is triggered when refresh token button is pressed
#  what it does is simulating a expiration in the access token refreshing it
#  against the api access token endpoint
@app.route('/refresh')
def refresh():

    credentials = json.loads(flask.session['credentials'])

    # notice the data sent to the endpoint differs here
    data = {'client_secret': CLIENT_SECRET,
            'grant_type': 'refresh_token', # it is request a Refresh Token flow
            'refresh_token': credentials['refresh_token'], # and sending the refresh token (it never changes)
            'client_id': CLIENT_ID}

    response = requests.post(API_ACCESS_TOKEN_ENDPOINT, data=data)
    new_credentials = json.loads(response.text)

    # updating current credentials
    credentials['access_token'] = new_credentials['access_token']
    credentials['token_type'] = new_credentials['token_type']
    credentials['expires_in'] = new_credentials['expires_in']
    flask.session['credentials'] = json.dumps(credentials)

    return flask.redirect(flask.url_for('index'))


if __name__ == '__main__':
    app.secret_key = str(uuid.uuid4())
    app.debug = True
    app.run()