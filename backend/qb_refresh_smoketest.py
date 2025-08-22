# qb_refresh_smoketest.py
import os
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load .env from project root deterministically
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH if ENV_PATH.exists() else None)

cid = os.getenv("QB_CLIENT_ID")
sec = os.getenv("QB_CLIENT_SECRET")
rt = os.getenv("QB_REFRESH_TOKEN")

if not all([cid, sec, rt]):
    logger.critical("Missing QB_CLIENT_ID / QB_CLIENT_SECRET / QB_REFRESH_TOKEN in .env")
    raise SystemExit("Missing QB_CLIENT_ID / QB_CLIENT_SECRET / QB_REFRESH_TOKEN in .env")

auth = base64.b64encode(f"{cid}:{sec}".encode()).decode()

logger.info("Attempting to perform a QuickBooks token refresh smoketest.")
try:
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
    resp.raise_for_status()
    
    logger.info(f"Response Status Code: {resp.status_code}")
    logger.info(f"Response Text: {resp.text[:1000]}")
    logger.info("QuickBooks token refresh smoketest successful.")

except requests.exceptions.RequestException as e:
    logger.error(f"An error occurred during the smoketest: {e}", exc_info=True)
    logger.error("QuickBooks token refresh smoketest failed.")
except Exception as e:
    logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
    logger.error("QuickBooks token refresh smoketest failed.")