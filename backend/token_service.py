# backend/token_service.py

from __future__ import annotations
import os, json, time
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from requests.auth import HTTPBasicAuth
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# ──────────────────────────────────────────────────────────────────────────────
# Env + paths
# ──────────────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH if ENV_PATH.exists() else None)

TOKENS_FILE = Path(os.getenv("TOKENS_FILE", PROJECT_ROOT / "backend/.tokens.json"))

def _read_tokens() -> Dict[str, Dict[str, Any]]:
    try:
        if TOKENS_FILE.exists():
            return json.loads(TOKENS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}

def _write_tokens(data: Dict[str, Dict[str, Any]]) -> None:
    TOKENS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKENS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def _now() -> int:
    return int(time.time())

def _persist_qb_tokens_from_oauth(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Persist tokens from an Intuit OAuth response and compute expirations.
    """
    at = body.get("access_token")
    rt = body.get("refresh_token")
    if not at or not rt:
        raise HTTPException(status_code=500, detail=f"QuickBooks response missing tokens: {body}")

    # Intuit returns seconds
    access_expires_at = _now() + int(body.get("expires_in", 3600)) - 60  # 1-min skew
    # Refresh token is typically 100 days (8,640,000s) in dev; fall back if missing
    refresh_expires_at = _now() + int(body.get("x_refresh_token_expires_in", 8640000)) - 300

    data = _read_tokens()
    data["quickbooks"] = {
        "access_token": at,
        "refresh_token": rt,
        "access_expires_at": access_expires_at,
        "refresh_expires_at": refresh_expires_at,
    }
    _write_tokens(data)
    return data["quickbooks"]

def get_token_for_provider(provider: str) -> Optional[Dict[str, Any]]:
    return _read_tokens().get(provider)

def set_token_for_provider(provider: str, access_token: str, refresh_token: Optional[str] = None) -> Dict[str, Any]:
    data = _read_tokens()
    entry: Dict[str, Any] = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        # If set manually, give short lifetimes so wrapper will refresh soon
        "access_expires_at": _now() + 1200,         # 20 min
        "refresh_expires_at": _now() + 8640000 - 300,  # ~100d - 5m
    }
    data[provider] = entry
    _write_tokens(data)
    return entry

# ──────────────────────────────────────────────────────────────────────────────
# QuickBooks OAuth
# ──────────────────────────────────────────────────────────────────────────────
QB_TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
QB_AUTH_URL = "https://appcenter.intuit.com/connect/oauth2"
QB_CLIENT_ID = os.getenv("QB_CLIENT_ID")
QB_CLIENT_SECRET = os.getenv("QB_CLIENT_SECRET")
QB_REALM_ID = os.getenv("QB_REALM_ID")
QB_REDIRECT_URI = os.getenv("QB_REDIRECT_URI")

def _ensure_qb_prereqs():
    if not QB_CLIENT_ID or not QB_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="QB_CLIENT_ID/QB_CLIENT_SECRET missing.")

def _refresh_qb(refresh_token: str) -> Dict[str, Any]:
    _ensure_qb_prereqs()
    headers = {"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    resp = requests.post(QB_TOKEN_URL, headers=headers, data=data, auth=HTTPBasicAuth(QB_CLIENT_ID, QB_CLIENT_SECRET), timeout=20)
    if resp.status_code != 200:
        msg = resp.text
        if "invalid_grant" in msg:
            msg += " | Hint: The refresh token is invalid/expired or from a different app/env. Re-authorize."
        raise HTTPException(status_code=500, detail=f"QuickBooks token refresh failed: {msg}")
    return _persist_qb_tokens_from_oauth(resp.json())

def refresh_token_for_provider(provider: str) -> Dict[str, Any]:
    if provider.lower() != "quickbooks":
        # simple stub for others
        import time
        cur = _read_tokens().get(provider, {})
        entry = {
            "access_token": f"{provider}_access_{int(time.time())}",
            "refresh_token": cur.get("refresh_token") or f"{provider}_refresh_{int(time.time())}",
            "access_expires_at": _now() + 3600,
            "refresh_expires_at": _now() + 8640000,
        }
        set_token_for_provider(provider, entry["access_token"], entry["refresh_token"])
        return entry

    _ensure_qb_prereqs()
    store = get_token_for_provider("quickbooks") or {}
    rt = store.get("refresh_token") or os.getenv("QB_REFRESH_TOKEN")
    if not rt:
        raise HTTPException(status_code=400, detail="No QuickBooks refresh_token found. Re-authorize and set tokens first.")
    return _refresh_qb(rt)

# ──────────────────────────────────────────────────────────────────────────────
# FastAPI
# ──────────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Token Service", version="1.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TokenSetRequest(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None

class QBCodeExchangeRequest(BaseModel):
    code: str
    redirect_uri: Optional[str] = None

@app.get("/api/token/{provider}")
def http_get_tokens(provider: str) -> Dict[str, Any]:
    tok = get_token_for_provider(provider)
    if not tok:
        raise HTTPException(status_code=404, detail=f"No tokens stored for provider '{provider}'.")
    return tok

@app.post("/api/token/{provider}/set")
def http_set_tokens(provider: str, payload: TokenSetRequest) -> Dict[str, Any]:
    return set_token_for_provider(provider, payload.access_token, payload.refresh_token)

@app.post("/api/token/{provider}/refresh")
def http_refresh_tokens(provider: str) -> Dict[str, Any]:
    return refresh_token_for_provider(provider)

# New: return the OAuth authorize URL so you can just click it
@app.get("/api/token/quickbooks/authorize")
def qb_authorize_url(state: str = "xyz") -> Dict[str, str]:
    _ensure_qb_prereqs()
    if not QB_REDIRECT_URI:
        raise HTTPException(status_code=500, detail="QB_REDIRECT_URI missing.")
    from urllib.parse import quote
    url = (
        f"{QB_AUTH_URL}?client_id={QB_CLIENT_ID}"
        f"&scope=com.intuit.quickbooks.accounting"
        f"&redirect_uri={quote(QB_REDIRECT_URI, safe='')}"
        f"&response_type=code&state={state}"
    )
    return {"authorize_url": url}

@app.post("/api/token/quickbooks/exchange")
def qb_exchange_code(payload: QBCodeExchangeRequest) -> Dict[str, Any]:
    _ensure_qb_prereqs()
    redirect_uri = payload.redirect_uri or QB_REDIRECT_URI
    if not payload.code or not redirect_uri:
        raise HTTPException(status_code=400, detail="Missing 'code' or 'redirect_uri'.")

    headers = {"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "authorization_code", "code": payload.code, "redirect_uri": redirect_uri}
    resp = requests.post(QB_TOKEN_URL, headers=headers, data=data, auth=HTTPBasicAuth(QB_CLIENT_ID, QB_CLIENT_SECRET), timeout=20)
    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail=f"QuickBooks code exchange failed: {resp.text}")
    return _persist_qb_tokens_from_oauth(resp.json())

# Bootstrap once from .env if provided
def _bootstrap_from_env_if_empty() -> None:
    if not get_token_for_provider("quickbooks"):
        at = os.getenv("QB_ACCESS_TOKEN")
        rt = os.getenv("QB_REFRESH_TOKEN")
        if at and rt:
            set_token_for_provider("quickbooks", at, rt)
_bootstrap_from_env_if_empty()
