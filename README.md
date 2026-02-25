# AI-Powered Gmail Spam Detection System (Scaffold)

This repository is a scaffolded, senior-designed implementation outline for an AI-powered Gmail spam detection system.

Quick start (local demo using mock emails):

1. Create a Python venv and install dependencies:

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. Train the demo model (uses training/dataset.csv):

```bash
python training/train_model.py
```

3. Start the backend server:

```bash
python backend/app.py
```

4. Open the frontend: [frontend/index.html](frontend/index.html)

To enable real Gmail fetching:
1. Create a Google OAuth client for a Web application in Google Cloud Console and download `client_secrets.json`.
2. Place the file at `backend/client_secrets.json` or set the `CLIENT_SECRETS_FILE` env var to its path.
3. Start the backend and open `/login` to perform the OAuth flow. The token will be saved to `backend/token.json`.

Notes:
- OAuth flow and real Gmail API calls require setting up credentials; the scaffold includes the auth blueprint.
- The training script uses TF-IDF + LogisticRegression and saves artifacts to `backend/model/`.
- `backend/sample_emails.json` is used as mock data if Gmail is not configured.

Security:
- Do NOT commit OAuth client secrets. Use env vars or a secure secret manager.
- Use HTTPS in production and the least-privilege scopes (gmail.readonly).
