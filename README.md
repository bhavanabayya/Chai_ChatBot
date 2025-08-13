
# Project Setup & Token Management Guide

## 1. Create & Activate Virtual Environment

```bash
python -m venv .venv
```

- On **Windows (PowerShell)**:
```powershell
.venv\Scripts\Activate.ps1
```

- On **macOS/Linux**:
```bash
source .venv/bin/activate
```

---

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 3. QuickBooks Token Smoke Test

This step is meant as a sanity check to see if your QuickBooks token refresh flow is actually working before you run the full chatbot.

```bash
python qb_refresh_smoketest.py
```

---

## 4. Start the Backend

Run the **token service**:
```bash
uvicorn backend.token_service:app --reload --port 8000
```

Run the **main chatbot backend**:
```bash
uvicorn backend.main:app --reload --port 8001
```

---

## 5. Launch the Frontend

```bash
streamlit run frontend/app.py
```

---

## 6. Token Management (QuickBooks)

The code in the `chatbot_fastapi_tools_tokens` branch uses `token_service.py`, a FastAPI microservice, to manage and refresh QuickBooks API tokens.

- When the `access_token` (valid for 1 hour) expires, the backend automatically detects a `401 Unauthorized` response and triggers a refresh by calling the `/token/refresh` endpoint on `http://localhost:8000`.
- This uses the `refresh_token` (valid for 100 days) to get a new access token from Intuit's servers.

### To view the latest tokens:
```bash
curl http://localhost:8000/token
```

This will return the current `access_token` and `refresh_token` in JSON format.

Make sure `token_service.py` is running locally using:
```bash
uvicorn backend.token_service:app --reload --port 8000
```

If the refresh token itself expires (rare, after long inactivity), a manual re-authentication via browser is required to obtain new credentials.

---

## 7. How to Reset Tokens

- Delete the `.tokens.json` file:
```bash
# Linux/Mac
rm backend/.tokens.json

# Windows
del backend\.tokens.json
```

- Restart the token service:
```bash
uvicorn backend.token_service:app --reload --port 8000
```
## 1) Remove any stale token file
*Windows (PowerShell)*:
powershell
del backend\.tokens.json -ErrorAction Ignore

*Mac/Linux*:
bash
rm -f backend/.tokens.json


---

## 2) Start the Token Service
bash
uvicorn backend.token_service:app --reload --port 8000


Keep this window running.

---

## 3) Get new tokens (programmatic, reliable)

### 3.1 Get the authorize URL
bash
curl http://localhost:8000/api/token/quickbooks/authorize

Copy the value of authorize_url from the JSON and open it in a browser.

### 3.2 Approve in Intuit & capture the code
After login & consent you’ll be redirected to a URL like:

http://localhost:8000/api/token/quickbooks/callback?code=ABCD1234XYZ&state=xyz&realmId=934145507451467

Copy *only* the value after code= and *stop before* &state.
Example code: ABCD1234XYZ

### 3.3 Exchange the code for tokens
*Windows (PowerShell)*:
powershell
$code = "ABCD1234XYZ"
$body = @{ code = $code } | ConvertTo-Json
Invoke-RestMethod `
  -Method POST `
  -Uri "http://localhost:8000/api/token/quickbooks/exchange" `
  -ContentType "application/json" `
  -Body $body

*Mac/Linux (curl)*:
bash
curl -X POST "http://localhost:8000/api/token/quickbooks/exchange"   -H "Content-Type: application/json"   -d '{"code":"ABCD1234XYZ"}'


Result: the service writes fresh tokens to backend/.tokens.json:
json
{
  "quickbooks": {
    "access_token": "...",
    "refresh_token": "...",
    "expires_at": 1723549872,
    "realm_id": "934145507451467"
  }
}


---

## 4) (Optional) Force a refresh later
bash
curl -X POST http://localhost:8000/api/token/quickbooks/refresh


---
- Re-run the **Authorize** → **Exchange** steps.

---

## 8. Deactivating the Environment

When you are finished working on the project, you can deactivate the environment and return to your global Python context by simply running:
```bash
deactivate
```

---

## 9. Error Handling Tips

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Expired access token | Ensure token service is running; it should refresh automatically |
| `invalid_grant` | Expired/invalid refresh token | Delete `.tokens.json` and re-authorize |
| `connection refused` | Token service not running | Start it with `uvicorn backend.token_service:app --reload --port 8000` |
| `file not found` | `.tokens.json` missing | Re-run the authorization flow |

---

## 10. Environment Variables (`.env`)

Your `.env` file must include:
```env
QUICKBOOKS_CLIENT_ID=your_client_id
QUICKBOOKS_CLIENT_SECRET=your_client_secret
QUICKBOOKS_REDIRECT_URI=http://localhost:8000/api/token/quickbooks/callback
QUICKBOOKS_ENVIRONMENT=sandbox
```

---

**Now you are ready to run the chatbot with automatic QuickBooks token refresh!**
