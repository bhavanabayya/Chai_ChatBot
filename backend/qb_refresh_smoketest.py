# qb_refresh_smoketest.py
import os
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root deterministically
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH if ENV_PATH.exists() else None)

cid = os.getenv("QB_CLIENT_ID")
sec = os.getenv("QB_CLIENT_SECRET")
rt  = os.getenv("QB_REFRESH_TOKEN")

if not all([cid, sec, rt]):
    raise SystemExit("Missing QB_CLIENT_ID / QB_CLIENT_SECRET / QB_REFRESH_TOKEN in .env")

auth = base64.b64encode(f"{cid}:{sec}".encode()).decode()

resp = requests.post(
    "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer",
    headers={
        "Authorization": f"Basic {auth}",
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    },
    data={"grant_type": "refresh_token", "refresh_token": rt},
    timeout=20,
)

print(resp.status_code)
print(resp.text[:1000])
