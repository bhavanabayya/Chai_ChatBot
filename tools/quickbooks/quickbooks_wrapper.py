import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from pathlib import Path

#  Resolve absolute path to .env and load it
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class QuickBooksWrapper:
    def __init__(self):
        self.base_url = "https://sandbox-quickbooks.api.intuit.com"
        self.token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
        self.client_id = os.getenv("QB_CLIENT_ID")
        self.client_secret = os.getenv("QB_CLIENT_SECRET")
        self.realm_id = os.getenv("QB_REALM_ID")

        # Load tokens fresh every time to ensure you're not using stale ones
        self._load_tokens()

    def _load_tokens(self):
        try:
            res = requests.get("http://localhost:8000/token")
            if res.status_code != 200:
                raise Exception("Failed to get token from service.")
            data = res.json()
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
        except Exception as e:
            raise Exception(f"Token loading failed: {e}")

    def _refresh_access_token(self):
        try:
            res = requests.post("http://localhost:8000/token/refresh")
            if res.status_code != 200:
                raise Exception("Token refresh request failed.")
            data = res.json()
            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
            print("🔁 Refreshed token from central service.")
        except Exception as e:
            raise Exception(f"Token refresh failed: {e}")

    def _save_tokens(self):
        with open(env_path, "r") as f:
            lines = f.readlines()

        with open(env_path, "w") as f:
            for line in lines:
                if line.startswith("QB_ACCESS_TOKEN="):
                    f.write(f"QB_ACCESS_TOKEN={self.access_token}\n")
                elif line.startswith("QB_REFRESH_TOKEN="):
                    f.write(f"QB_REFRESH_TOKEN={self.refresh_token}\n")
                else:
                    f.write(line)

    def _make_authenticated_request(self, method, url, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        headers.setdefault("Accept", "application/json")
        kwargs["headers"] = headers
        response = requests.request(method, url, timeout=10, **kwargs)

        # response = requests.request(method, url, **kwargs)

        # If token expired, refresh and retry once
        if response.status_code == 401:
            print(" Access token expired. Refreshing...")
            self._refresh_access_token()
            headers["Authorization"] = f"Bearer {self.access_token}"
            kwargs["headers"] = headers
            response = requests.request(method, url, **kwargs)

        return response

    def create_invoice(self, customer_id, line_items):
        url = f"{self.base_url}/v3/company/{self.realm_id}/invoice?minorversion=75"
        body = {
            "Line": line_items,
            "CustomerRef": {"value": customer_id}
        }
        headers = {"Content-Type": "application/json"}
        response = self._make_authenticated_request("POST", url, json=body, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"QuickBooks Error: {response.status_code} - {response.text}")

    def get_invoice_pdf(self, invoice_id):
        url = f"{self.base_url}/v3/company/{self.realm_id}/invoice/{invoice_id}/pdf"
        headers = {"Accept": "application/pdf"}
        response = self._make_authenticated_request("GET", url, headers=headers)

        if response.status_code == 200:
            return response.content  #  Return PDF bytes to stream via FastAPI
        else:
            raise Exception(f"PDF fetch failed: {response.status_code} - {response.text}")
