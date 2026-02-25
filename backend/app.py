from flask import Flask, request, jsonify, send_from_directory
from flask_session import Session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from pathlib import Path
import joblib
from backend import preprocessing
from backend.gmail_fetch import fetch_emails
from backend.auth import bp as auth_bp

app = Flask(__name__, static_folder=str(Path(__file__).parent.parent / 'frontend'))
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret')
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
# CORS
CORS(app, origins=os.environ.get('CORS_ORIGINS', '*'))
# Rate limiting (create limiter and initialize with app to avoid positional-arg clash)
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
limiter.init_app(app)
app.register_blueprint(auth_bp)

MODEL_DIR = Path(__file__).parent / 'model'
MODEL_PATH = MODEL_DIR / 'spam_model.pkl'
VECT_PATH = MODEL_DIR / 'vectorizer.pkl'

model = None
vectorizer = None


def load_model():
    global model, vectorizer
    if MODEL_PATH.exists() and VECT_PATH.exists():
        model = joblib.load(MODEL_PATH)
        vectorizer = joblib.load(VECT_PATH)
    else:
        model = None
        vectorizer = None


@app.route('/')
def index():
    return 'AI-Powered Gmail Spam Detection Backend'


@app.route('/fetch-emails')
@limiter.limit("10/minute")
def route_fetch_emails():
    emails = fetch_emails()
    return jsonify({'count': len(emails), 'emails': emails})


@app.route('/')
def serve_frontend():
    # serve frontend index.html
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)


@app.route('/analyze', methods=['POST'])
def analyze():
    load_model()
    if model is None or vectorizer is None:
        return jsonify({'error': 'Model not found. Train model first using training/train_model.py'}), 400
    data = request.get_json() or {}
    emails = data.get('emails')
    if emails is None:
        return jsonify({'error': 'Provide JSON body with `emails`: [ {subject, sender, date, body} ]'}), 400
    results = []
    bodies = [preprocessing.clean_text(e.get('body','') or e.get('snippet','')) for e in emails]
    X = vectorizer.transform(bodies)
    probs = model.predict_proba(X)
    labels = model.classes_
    feature_names = []
    try:
        feature_names = list(vectorizer.get_feature_names_out())
    except Exception:
        feature_names = []
    for i, e in enumerate(emails):
        spam_idx = list(labels).index('spam') if 'spam' in labels else -1
        prob_spam = float(probs[i][spam_idx]) if spam_idx!=-1 else float(probs[i].max())
        label = 'spam' if prob_spam >= 0.5 else 'not_spam'
        # risk level
        if prob_spam < 0.3:
            risk = 'low'
        elif prob_spam < 0.7:
            risk = 'medium'
        else:
            risk = 'high'
        # suspicious keywords: top TF-IDF features in the email
        suspicious = []
        try:
            row = X[i]
            if feature_names:
                import numpy as np
                arr = row.toarray().ravel()
                top_idx = np.argsort(arr)[-5:][::-1]
                suspicious = [feature_names[j] for j in top_idx if arr[j] > 0][:5]
        except Exception:
            suspicious = []
        results.append({
            'subject': e.get('subject'),
            'sender': e.get('sender'),
            'date': e.get('date'),
            'label': label,
            'probability': round(prob_spam, 4),
            'risk': risk,
            'suspicious_words': suspicious
        })
    return jsonify({'results': results})


@app.route('/dashboard')
def dashboard():
    load_model()
    emails = fetch_emails()
    if model is None or vectorizer is None:
        return jsonify({'error':'Model not found. Train model first.'}), 400
    bodies = [preprocessing.clean_text(e.get('body','') or e.get('snippet','')) for e in emails]
    X = vectorizer.transform(bodies)
    probs = model.predict_proba(X)
    labels = model.classes_
    spam_idx = list(labels).index('spam') if 'spam' in labels else -1
    spam_count = 0
    keywords = {}
    for i in range(len(emails)):
        prob_spam = float(probs[i][spam_idx]) if spam_idx!=-1 else float(probs[i].max())
        if prob_spam >= 0.5:
            spam_count += 1
        # collect suspicious words
        try:
            row = X[i]
            feature_names = list(vectorizer.get_feature_names_out())
            arr = row.toarray().ravel()
            import numpy as np
            top_idx = np.argsort(arr)[-5:][::-1]
            for j in top_idx:
                if arr[j] > 0:
                    w = feature_names[j]
                    keywords[w] = keywords.get(w, 0) + 1
        except Exception:
            pass
    total = len(emails)
    spam_pct = round((spam_count/total)*100,2) if total>0 else 0.0
    # top keywords
    top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]
    return jsonify({'total_emails': total, 'spam_count': spam_count, 'spam_percentage': spam_pct, 'top_keywords': top_keywords})


if __name__ == '__main__':
    load_model()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
