# 🍵 Chai Chatbot – Setup & Token Management

This guide explains how to set up the environment, run the backend/frontend, and manage QuickBooks tokens with the **token service**.

---

## 1. Virtual Environment (Backend)

From the **`backend`** folder:

```bash
python -m venv .venv
```

Activate:

- **Windows (PowerShell)**  
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **macOS/Linux**  
  ```bash
  source .venv/bin/activate
  ```

---

## 2. Install Dependencies (Backend)

```bash
pip install -r requirements.txt
```

---

## 3. QuickBooks Token Service

A FastAPI microservice (`token_service.py`) manages QuickBooks tokens.

### Start the Token Service
```bash
cd backend
uvicorn token_service:app --reload --port 8000
```

### Authorize QuickBooks (First-Time Setup or Expired Refresh Token)

1. Get authorize URL:  
   ```bash
   curl http://127.0.0.1:8000/api/token/quickbooks/authorize
   ```
   Open the returned `authorize_url` in a browser.
    To get the whole url run the below command in your terminal (new one):
    ```bash
   curl http://127.0.0.1:8000/api/token/quickbooks/authorize | ConvertFrom-Json | Select-Object -ExpandProperty authorize_url
   ```
2. Log in to QuickBooks Sandbox and approve the app.  
   You’ll be redirected to:
   ```
   http://localhost:8000/api/token/quickbooks/callback?code=...&state=xyz&realmId=...
   ```

3. The service exchanges the code and writes tokens to:
   ```
   backend/.tokens.json
   ```

4. Verify:  
   ```bash
   curl http://127.0.0.1:8000/api/token/quickbooks
   ```

### Refresh Tokens

- Access tokens expire every hour.  
- The backend automatically refreshes using the stored refresh token (~100 days).  
- If the refresh token expires → delete `.tokens.json` and re-authorize.

---

## 4. Main Backend

Run in a separate terminal:

```bash
cd backend
uvicorn main:app --reload --port 8001
```

---

## 5. Frontend

From the **`frontend`** folder:

```bash
npm install
npm run dev
```

---

## 6. Environment Files

Keep **two separate `.env` files**:

### `frontend/.env`
For browser-safe keys (Vite requires `VITE_` prefix):

```env
VITE_PAYPAL_CLIENT_ID=your_paypal_client_id
VITE_STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key

VITE_BACKEND_URL=http://127.0.0.1:8001
```

---

### `backend/.env`
For secrets (FastAPI only):

```env
# URLs / CORS
BACKEND_URL=http://127.0.0.1:8001
FRONTEND_URL=http://127.0.0.1:5173
CORS_ALLOW_ORIGINS=http://127.0.0.1:5173

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_API_MODEL=gpt-4o-mini

# QuickBooks
QB_CLIENT_ID=...
QB_CLIENT_SECRET=...
QB_REDIRECT_URI=http://127.0.0.1:8000/api/token/quickbooks/callback
QB_ENVIRONMENT=sandbox

# PayPal
PAYPAL_CLIENT_ID=...
PAYPAL_CLIENT_SECRET=...

# Stripe
STRIPE_SECRET_KEY=sk_test_...

# FedEx (if used)
FEDEX_CLIENT_ID=...
FEDEX_CLIENT_SECRET=...
FEDEX_ACCOUNT_NUMBER=...

# Optional
QB_MINOR_VERSION=75
```

 **Do not** put `QB_ACCESS_TOKEN` or `QB_REFRESH_TOKEN` in `.env` → they are stored in `backend/.tokens.json`.

---

## 7. Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Expired access token | Auto-refreshes, or call `/refresh` |
| `invalid_grant` | Refresh token expired | Delete `.tokens.json` and re-authorize |
| `connection refused` | Token service not running | Start with `uvicorn token_service:app` |
| `file not found` | `.tokens.json` missing | Run authorize flow again |

---

## 8. Shut Down

When finished:

```bash
deactivate
```
