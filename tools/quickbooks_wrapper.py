import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

class QuickBooksWrapper:
    def __init__(self):
        self.base_url = "https://sandbox-quickbooks.api.intuit.com"
        self.token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
        self.client_id = os.getenv("QB_CLIENT_ID")
        self.client_secret = os.getenv("QB_CLIENT_SECRET")
        self.refresh_token = os.getenv("QB_REFRESH_TOKEN")
        self.access_token = os.getenv("QB_ACCESS_TOKEN")
        self.realm_id = os.getenv("QB_REALM_ID")

    def _refresh_access_token(self):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        auth = HTTPBasicAuth(self.client_id, self.client_secret)
        response = requests.post(self.token_url, headers=headers, data=data, auth=auth)

        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens["access_token"]
            self.refresh_token = tokens.get("refresh_token", self.refresh_token)
            self._save_tokens()
        else:
            raise Exception(f"Failed to refresh token: {response.status_code} - {response.text}")

    def _save_tokens(self):
        with open(".env", "r") as f:
            lines = f.readlines()
        with open(".env", "w") as f:
            for line in lines:
                if line.startswith("QB_ACCESS_TOKEN"):
                    f.write(f"QB_ACCESS_TOKEN={self.access_token}\n")
                elif line.startswith("QB_REFRESH_TOKEN"):
                    f.write(f"QB_REFRESH_TOKEN={self.refresh_token}\n")
                else:
                    f.write(line)

    def _make_authenticated_request(self, method, url, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        headers.setdefault("Accept", "application/json")
        kwargs["headers"] = headers

        response = requests.request(method, url, **kwargs)
        if response.status_code == 401:
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
            file_name = f"invoice_{invoice_id}.pdf"
            with open(file_name, "wb") as f:
                f.write(response.content)
            return f"Invoice PDF saved as {file_name}"
        else:
            raise Exception(f"PDF fetch failed: {response.status_code} - {response.text}")
