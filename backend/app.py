import os
from pathlib import Path

import joblib
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_session import Session

try:
    from backend import preprocessing
    from backend.auth import bp as auth_bp
    from backend.gmail_fetch import fetch_emails
except ModuleNotFoundError:
    import preprocessing
    from auth import bp as auth_bp
    from gmail_fetch import fetch_emails

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / 'model'
MODEL_PATH = MODEL_DIR / 'spam_model.pkl'
VECT_PATH = MODEL_DIR / 'vectorizer.pkl'


app = Flask(__name__, static_folder=str(BASE_DIR.parent / 'frontend'))
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret-change-me')
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

CORS(app, origins=os.environ.get('CORS_ORIGINS', '*'))
limiter = Limiter(key_func=get_remote_address, default_limits=['200 per day', '50 per hour'])
limiter.init_app(app)
app.register_blueprint(auth_bp)

model = None
vectorizer = None


def load_model(force_reload: bool = False):
    """Load trained model artifacts into memory."""
    global model, vectorizer
    if model is not None and vectorizer is not None and not force_reload:
        return
    if MODEL_PATH.exists() and VECT_PATH.exists():
        model = joblib.load(MODEL_PATH)
        vectorizer = joblib.load(VECT_PATH)
    else:
        model = None
        vectorizer = None


def _predict_emails(emails):
    if model is None or vectorizer is None:
        return None

    bodies = [preprocessing.clean_text(e.get('body', '') or e.get('snippet', '')) for e in emails]
    X = vectorizer.transform(bodies)
    probs = model.predict_proba(X)
    labels = list(model.classes_)
    spam_idx = labels.index('spam') if 'spam' in labels else -1

    feature_names = []
    try:
        feature_names = list(vectorizer.get_feature_names_out())
    except Exception:
        feature_names = []

    results = []
    for i, email in enumerate(emails):
        prob_spam = float(probs[i][spam_idx]) if spam_idx != -1 else float(max(probs[i]))
        label = 'spam' if prob_spam >= 0.5 else 'not_spam'
        risk = 'low' if prob_spam < 0.3 else ('medium' if prob_spam < 0.7 else 'high')

        suspicious = []
        try:
            import numpy as np

            row = X[i].toarray().ravel()
            if feature_names:
                top_idx = np.argsort(row)[-6:][::-1]
                suspicious = [feature_names[j] for j in top_idx if row[j] > 0][:6]
        except Exception:
            suspicious = []

        results.append(
            {
                'subject': email.get('subject', '(No Subject)'),
                'sender': email.get('sender', 'Unknown Sender'),
                'date': email.get('date', ''),
                'label': label,
                'probability': round(prob_spam, 4),
                'risk': risk,
                'suspicious_words': suspicious,
            }
        )

    return results


def _dashboard_from_results(results):
    total = len(results)
    spam_count = sum(1 for row in results if row['label'] == 'spam')
    spam_pct = round((spam_count / total) * 100, 2) if total else 0.0

    keywords = {}
    for row in results:
        for word in row.get('suspicious_words', []):
            keywords[word] = keywords.get(word, 0) + 1

    top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]
    return {
        'total_emails': total,
        'spam_count': spam_count,
        'spam_percentage': spam_pct,
        'top_keywords': top_keywords,
    }


@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)


@app.route('/health')
def health():
    load_model()
    return jsonify(
        {
            'status': 'ok',
            'model_loaded': model is not None and vectorizer is not None,
            'model_path': str(MODEL_PATH),
            'vectorizer_path': str(VECT_PATH),
        }
    )


@app.route('/fetch-emails')
@limiter.limit('15/minute')
def route_fetch_emails():
    emails = fetch_emails()
    return jsonify({'count': len(emails), 'emails': emails})


@app.route('/analyze', methods=['POST'])
@limiter.limit('25/minute')
def analyze():
    load_model()
    if model is None or vectorizer is None:
        return jsonify({'error': 'Model not found. Train model first using training/train_model.py'}), 400

    data = request.get_json() or {}
    emails = data.get('emails')
    if emails is None or not isinstance(emails, list):
        return jsonify({'error': 'Provide JSON body with `emails`: [ {subject, sender, date, body} ]'}), 400

    results = _predict_emails(emails)
    return jsonify({'results': results, 'summary': _dashboard_from_results(results)})


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    load_model()
    if model is None or vectorizer is None:
        return jsonify({'error': 'Model not found. Train model first.'}), 400

    if request.method == 'POST':
        payload = request.get_json() or {}
        emails = payload.get('emails', [])
    else:
        emails = fetch_emails()

    results = _predict_emails(emails)
    return jsonify(_dashboard_from_results(results))


@app.route('/reload-model', methods=['POST'])
def reload_model():
    load_model(force_reload=True)
    if model is None or vectorizer is None:
        return jsonify({'status': 'error', 'message': 'Model files missing.'}), 400
    return jsonify({'status': 'ok', 'message': 'Model reloaded successfully.'})


if __name__ == '__main__':
    load_model()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
