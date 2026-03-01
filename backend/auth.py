import os
from urllib.parse import urlparse

from flask import Blueprint, redirect, request, session, url_for, jsonify
from google_auth_oauthlib.flow import Flow

bp = Blueprint('auth', __name__)

CLIENT_SECRETS_FILE = os.environ.get('CLIENT_SECRETS_FILE', os.path.join(os.path.dirname(__file__), 'client_secrets.json'))
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'openid', 'https://www.googleapis.com/auth/userinfo.email']
TOKEN_PATH = os.path.join(os.path.dirname(__file__), 'token.json')


def _normalize_uri(uri: str) -> str:
    return (uri or '').strip().rstrip('/')


def _resolve_redirect_uri() -> str:
    """Build redirect URI in a way that works behind reverse proxies."""
    override = _normalize_uri(os.environ.get('OAUTH_REDIRECT_URI', ''))
    if override:
        return override

    forwarded_proto = request.headers.get('X-Forwarded-Proto', request.scheme).split(',')[0].strip()
    forwarded_host = request.headers.get('X-Forwarded-Host', request.host).split(',')[0].strip()
    callback_path = url_for('auth.oauth2callback')
    return f'{forwarded_proto}://{forwarded_host}{callback_path}'


def _local_redirect_examples() -> list[str]:
    callback_path = url_for('auth.oauth2callback')
    return [
        f'http://localhost:5000{callback_path}',
        f'http://127.0.0.1:5000{callback_path}',
    ]


def _validate_redirect_shape(uri: str) -> str | None:
    parsed = urlparse(uri)
    if not parsed.scheme or not parsed.netloc:
        return 'Resolved redirect URI is invalid. Set OAUTH_REDIRECT_URI to a full URL.'
    if not parsed.path.endswith('/oauth2callback'):
        return 'Resolved redirect URI must end with /oauth2callback.'
    return None


@bp.route('/login')
def login():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        return jsonify({'error': 'CLIENT_SECRETS_FILE not found. Place client_secrets.json or set CLIENT_SECRETS_FILE env var.'}), 400

    redirect_uri = _resolve_redirect_uri()
    redirect_error = _validate_redirect_shape(redirect_uri)
    if redirect_error:
        return jsonify({'error': redirect_error, 'resolved_redirect_uri': redirect_uri, 'expected_examples': _local_redirect_examples()}), 400

    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = redirect_uri
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true', prompt='consent')
    session['oauth_state'] = state
    return redirect(authorization_url)


@bp.route('/oauth2callback')
def oauth2callback():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        return jsonify({'error': 'CLIENT_SECRETS_FILE not found.'}), 400

    redirect_uri = _resolve_redirect_uri()
    redirect_error = _validate_redirect_shape(redirect_uri)
    if redirect_error:
        return jsonify({'error': redirect_error, 'resolved_redirect_uri': redirect_uri, 'expected_examples': _local_redirect_examples()}), 400

    state = session.get('oauth_state')
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = redirect_uri
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


@bp.route('/oauth/debug')
def oauth_debug():
    resolved = _resolve_redirect_uri()
    return jsonify(
        {
            'resolved_redirect_uri': resolved,
            'oauth_redirect_override': os.environ.get('OAUTH_REDIRECT_URI', ''),
            'request_scheme': request.scheme,
            'request_host': request.host,
            'x_forwarded_proto': request.headers.get('X-Forwarded-Proto', ''),
            'x_forwarded_host': request.headers.get('X-Forwarded-Host', ''),
            'local_redirect_examples': _local_redirect_examples(),
            'google_console_tip': 'Add the exact resolved_redirect_uri value (including /oauth2callback) under Authorized redirect URIs in Google Cloud Console.',
            'resolved_shape_error': _validate_redirect_shape(resolved),
        }
    )
