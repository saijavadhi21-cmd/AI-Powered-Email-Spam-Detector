# AI-Powered Gmail Spam Detection System

Production-ready Flask + Bootstrap application for classifying Gmail messages as **spam** or **not spam** with explainable signals.

## What was improved
- ✅ End-to-end API and UI integration.
- ✅ Cleaner backend routes (`/health`, `/analyze`, `/dashboard`, `/reload-model`).
- ✅ Better analytics payloads for frontend rendering.
- ✅ Upgraded, attractive dashboard UI.
- ✅ Expanded training dataset to improve baseline quality.
- ✅ Deployment-ready app entrypoint (`backend/wsgi.py`) + `Procfile` + `Dockerfile`.
- ✅ Environment-driven production settings (`.env.example`).

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
- `GET /oauth/debug` → shows exact redirect URI resolved by backend.

## Gmail OAuth setup

1. Create a Web OAuth client in Google Cloud Console.
2. Download credentials JSON.
3. Set env var or place file at `backend/client_secrets.json`:

```bash
export CLIENT_SECRETS_FILE=/absolute/path/client_secrets.json
```

4. Set the callback URI explicitly when deploying behind HTTPS proxy/load balancer:

```bash
export OAUTH_REDIRECT_URI=https://your-domain.com/oauth2callback
```

5. In Google Cloud Console OAuth client settings, configure both sections correctly:
   - **Authorized JavaScript origins** (no path allowed):
     - `http://localhost:5000`
     - `http://127.0.0.1:5000`
   - **Authorized redirect URIs** (must include callback path):
     - `http://localhost:5000/oauth2callback`
     - `http://127.0.0.1:5000/oauth2callback`
   - ❌ Invalid origin example: `http://localhost:5000/oauth2callback` (path is not allowed in JavaScript origins)
6. Run server and open `/login`.

### Quick testing mode (skip Google OAuth)

If you only need to test the spam detector quickly (college demo / assignment), you can skip Google login:

1. Start backend normally (`python backend/app.py`).
2. Open `http://127.0.0.1:5000`.
3. Click **Use Demo Emails (No Google)**.
4. Click **Analyze with AI**.

This uses bundled sample inbox data and exercises the full ML pipeline without OAuth setup.

### If you see `Error 403: access_denied`

This usually means OAuth consent is not ready for your account yet (not a code bug).

1. Open **Google Cloud Console → APIs & Services → OAuth consent screen**.
2. If app status is **Testing**, add your Gmail account in **Test users**.
3. If app should be usable by anyone outside test users, complete consent verification and publish to **Production**.
4. Verify the callback URL in your OAuth client exactly matches your backend callback (for local default: `http://127.0.0.1:5000/oauth2callback`).

## Production Deployment

### Option A: Gunicorn (VM / Render / Railway / Heroku-style)

1. Create and configure environment variables (copy from `.env.example`).
2. Train model once and ensure artifacts exist:

```bash
python training/train_model.py
```

3. Start service:

```bash
gunicorn -w 2 -k gthread -b 0.0.0.0:${PORT:-5000} backend.wsgi:app
```

### Option B: Docker

```bash
docker build -t gmail-spam-detector .
docker run --env-file .env -p 5000:5000 gmail-spam-detector
```

### Required production env vars

- `FLASK_SECRET` (strong random secret)
- `CORS_ORIGINS` (your frontend domain)
- `CLIENT_SECRETS_FILE` (absolute path in runtime)
- `RATE_LIMIT_STORAGE_URI` (Redis URL, e.g. `redis://host:6379/0`)
- `OAUTH_REDIRECT_URI` (recommended for production to avoid redirect URI mismatch)

## Model details

- `TfidfVectorizer(max_features=5000)`
- `LogisticRegression(max_iter=1000)`
- Training data: `training/dataset.csv`
- Artifacts output: `backend/model/`

## Security notes

- Use least-privilege Gmail scopes (`gmail.readonly`).
- Do not commit OAuth credentials or production tokens.
- Rotate secrets and monitor API logs/rate-limit events.
