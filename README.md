# AI-Powered Gmail Spam Detection System

Production-ready Flask + Bootstrap application for classifying Gmail messages as **spam** or **not spam** with explainable signals.

## What was improved
- ✅ End-to-end API and UI integration.
- ✅ Cleaner backend routes (`/health`, `/analyze`, `/dashboard`, `/reload-model`).
- ✅ Better analytics payloads for frontend rendering.
- ✅ Upgraded, attractive dashboard UI.
- ✅ Expanded training dataset to improve baseline quality.

## Quick Start (Local)

1. **Install dependencies**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. **Train model artifacts**

```bash
python training/train_model.py
```

3. **Run backend server**

```bash
python backend/app.py
```

4. **Open app**

- http://127.0.0.1:5000

## API Endpoints

- `GET /` → frontend app.
- `GET /health` → backend/model health.
- `GET /fetch-emails` → Gmail inbox (or local sample fallback).
- `POST /analyze` → classify provided emails.
- `GET|POST /dashboard` → analytics summary.
- `POST /reload-model` → force in-memory model refresh.
- `GET /login`, `GET /oauth2callback`, `GET /logout` → Google OAuth flow.

## Gmail OAuth setup

1. Create a Web OAuth client in Google Cloud Console.
2. Download credentials JSON.
3. Set env var or place file at `backend/client_secrets.json`:

```bash
export CLIENT_SECRETS_FILE=/absolute/path/client_secrets.json
```

4. Run server and open `/login`.

## Deployment Checklist

- Set `FLASK_SECRET` to a secure random value.
- Set restrictive `CORS_ORIGINS`.
- Run with a production WSGI server (`gunicorn`/`uwsgi`).
- Configure HTTPS and reverse proxy.
- Keep OAuth secrets outside repository.

## Model details

- `TfidfVectorizer(max_features=5000)`
- `LogisticRegression(max_iter=1000)`
- Training data: `training/dataset.csv`
- Artifacts output: `backend/model/`

## Security notes

- Use least-privilege Gmail scopes (`gmail.readonly`).
- Do not commit OAuth credentials or production tokens.
- Rotate secrets and monitor API logs/rate-limit events.
