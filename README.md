
### 1. Create & Activate Virtual Environment

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

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 5. Start the Backend
```bash
uvicorn backend.token_service:app --reload --port 8000
```
```bash
uvicorn backend.main:app --reload --port 8001
```

---

### 6. Launch the Frontend

```bash
streamlit run frontend/app.py
```
---

---

## 7. Token Management (QuickBooks)

The code in the `chatbot_fastapi_tools_tokens` branch uses `token_service.py`, a FastAPI microservice, to manage and refresh QuickBooks API tokens.

- When the `access_token` (valid for 1 hour) expires, the backend automatically detects a `401 Unauthorized` response and triggers a refresh by calling the `/token/refresh` endpoint on `http://localhost:8000`.
- This uses the `refresh_token` (valid for 100 days) to get a new access token from Intuit's servers.

###  To view the latest tokens:
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
## 8. Deactivating the Environment

When you are finished working on the project, you can deactivate the environment and return to your global Python context by simply running:

`````deactivate`````
Follow the steps below to set up and run the project on your local machine.
