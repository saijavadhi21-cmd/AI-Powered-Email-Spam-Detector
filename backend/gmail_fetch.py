import os
import json
from pathlib import Path

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
except Exception:
    Credentials = None
    build = None


def _load_token():
    token_file = Path(__file__).parent / 'token.json'
    if token_file.exists():
        try:
            data = json.loads(token_file.read_text(encoding='utf-8'))
            return data
        except Exception:
            return None
    return None


def _fetch_from_gmail():
    if Credentials is None or build is None:
        return None
    token_data = _load_token()
    if not token_data:
        return None
    creds = Credentials.from_authorized_user_info(token_data, scopes=['https://www.googleapis.com/auth/gmail.readonly'])
    try:
        service = build('gmail', 'v1', credentials=creds)
        resp = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=50).execute()
        msgs = resp.get('messages', [])
        results = []
        for m in msgs:
            mid = m.get('id')
            full = service.users().messages().get(userId='me', id=mid, format='full').execute()
            headers = {h['name'].lower(): h.get('value') for h in full.get('payload', {}).get('headers', [])}
            snippet = full.get('snippet', '')
            subject = headers.get('subject')
            sender = headers.get('from')
            date = headers.get('date')
            body = ''
            payload = full.get('payload', {})
            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType','').startswith('text') and part.get('body', {}).get('data'):
                        import base64
                        data = part['body']['data']
                        try:
                            body = base64.urlsafe_b64decode(data.encode('utf-8')).decode('utf-8', errors='ignore')
                            break
                        except Exception:
                            continue
            results.append({'id': mid, 'subject': subject, 'sender': sender, 'date': date, 'body': body, 'snippet': snippet})
        return results
    except Exception:
        return None


def fetch_emails():
    gmail_results = _fetch_from_gmail()
    if gmail_results is not None:
        return gmail_results
    sample = Path(__file__).parent / 'sample_emails.json'
    if sample.exists():
        try:
            return json.loads(sample.read_text(encoding='utf-8'))
        except Exception:
            return []
    return []
