import os
import json
from flask import Blueprint, redirect, request, session, url_for, jsonify
from google_auth_oauthlib.flow import Flow

bp = Blueprint('auth', __name__)

CLIENT_SECRETS_FILE = os.environ.get('CLIENT_SECRETS_FILE', os.path.join(os.path.dirname(__file__), 'client_secrets.json'))
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'openid', 'https://www.googleapis.com/auth/userinfo.email']
TOKEN_PATH = os.path.join(os.path.dirname(__file__), 'token.json')


@bp.route('/login')
def login():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        return jsonify({'error': 'CLIENT_SECRETS_FILE not found. Place client_secrets.json or set CLIENT_SECRETS_FILE env var.'}), 400
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = request.url_root.rstrip('/') + url_for('auth.oauth2callback')
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true', prompt='consent')
    session['oauth_state'] = state
    return redirect(authorization_url)


@bp.route('/oauth2callback')
def oauth2callback():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        return jsonify({'error': 'CLIENT_SECRETS_FILE not found.'}), 400
    state = session.get('oauth_state')
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = request.url_root.rstrip('/') + url_for('auth.oauth2callback')
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)
    creds = flow.credentials
    with open(TOKEN_PATH, 'w') as f:
        f.write(creds.to_json())
    return jsonify({'message': 'OAuth completed and token saved to backend/token.json'})


@bp.route('/logout')
def logout():
    try:
        if os.path.exists(TOKEN_PATH):
            os.remove(TOKEN_PATH)
    except Exception:
        pass
    session.clear()
    return jsonify({'message': 'Logged out, token removed'})
