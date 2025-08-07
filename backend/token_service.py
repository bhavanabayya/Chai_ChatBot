# backend/token_service.py

import os
import requests
from fastapi import FastAPI, HTTPException
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from pydantic import BaseModel

# Load secrets from .env
load_dotenv()

CLIENT_ID = os.getenv("QB_CLIENT_ID")
CLIENT_SECRET = os.getenv("QB_CLIENT_SECRET")
REALM_ID = os.getenv("QB_REALM_ID")
TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"

# Start FastAPI app
app = FastAPI()

# In-memory storage (replace with DB or Redis in production)
TOKENS = {
    "access_token": os.getenv("QB_ACCESS_TOKEN"),
    "refresh_token": os.getenv("QB_REFRESH_TOKEN")
}

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str

@app.get("/token", response_model=TokenResponse)
def get_tokens():
    """Returns current QuickBooks tokens"""
    return TOKENS

@app.post("/token/refresh", response_model=TokenResponse)
def refresh_tokens():
    """Refreshes access token using refresh token"""
    data = {
        "grant_type": "refresh_token",
        "refresh_token": TOKENS["refresh_token"]
    }
    auth = HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    response = requests.post(TOKEN_URL, headers=headers, data=data, auth=auth)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Token refresh failed: {response.text}")

    token_data = response.json()
    TOKENS["access_token"] = token_data["access_token"]
    TOKENS["refresh_token"] = token_data.get("refresh_token", TOKENS["refresh_token"])

    print(" Token refreshed successfully.")
    return TOKENS
