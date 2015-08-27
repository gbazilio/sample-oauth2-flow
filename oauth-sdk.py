import os
import uuid
import flask
import httplib2

from flask import Flask
from flask import render_template

from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import OAuth2Credentials
from apiclient.discovery import build

app = Flask(__name__)

SCOPE = 'https://www.googleapis.com/auth/drive.readonly'

# both comes from Google API Console
#  after you have registered your applications
CLIENT_ID = os.environ['OAUTH_CLIENT_ID']
CLIENT_SECRET = os.environ['OAUTH_CLIENT_SECRET']

# url to redirect the user after authorization succeded or denied
REDIRECT_URI = 'http://localhost:5000/oauth2callback'

# Google API client
flow = OAuth2WebServerFlow(client_id=CLIENT_ID,
                           client_secret=CLIENT_SECRET,
                           scope=SCOPE,
                           redirect_uri=REDIRECT_URI)

# Authorization endpoint
API_AUTHORIZATION_ENDPOINT = flow.step1_get_authorize_url()


@app.route('/')
def index():

    if 'credentials' not in flask.session:
        return render_template('home.html')
    else:
        # code runs only if user has authorized the application
        credentials = OAuth2Credentials.from_json(flask.session['credentials'])
        
        # creates an authorized Http() object
        http_auth = credentials.authorize(httplib2.Http())

        # if we get here, it means what we all want: the Access Token
        #  so it is used to build the request to the private resource we want
        drive_service = build('drive', 'v2', http=http_auth)
        drive_files = drive_service.files().list().execute()

        return render_template('loggedin.html', results=drive_files, token=flask.session['credentials'])


# function triggered when user's click the login button
@app.route('/login')
def login():

    # credentials variable is manually created in session
    if 'credentials' not in flask.session:

        # code, while in response, is the authorization code sent from the api authorization server
        #  which in this case is the google api.
        #  if it is not part of the response, means the user has not allowed the app to access its resource yet
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

    # sends a request to exchange code by access token to the api authorization server
    credentials = flow.step2_exchange(authorization_code)
    
    flask.session['credentials'] = credentials.to_json()
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

    credentials = OAuth2Credentials.from_json(flask.session['credentials'])

    # notice the data sent to the endpoint differs here
    http_auth = credentials.authorize(httplib2.Http())
    credentials.refresh(http=http_auth)

    flask.session['credentials'] = credentials.to_json()

    return flask.redirect(flask.url_for('index'))


if __name__ == '__main__':
    app.secret_key = str(uuid.uuid4())
    app.debug = True
    app.run()