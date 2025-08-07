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
        load_dotenv(dotenv_path=env_path)  # re-load updated values
        self.access_token = os.getenv("QB_ACCESS_TOKEN")
        self.refresh_token = os.getenv("QB_REFRESH_TOKEN")

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
            self._load_tokens()  # ensure tokens in memory are fresh
            print(" QuickBooks tokens refreshed.")
        else:
            raise Exception(f"Failed to refresh token: {response.status_code} - {response.text}")

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

        response = requests.request(method, url, **kwargs)

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
        
    def find_customer_by_name(self, full_name: str):
        url = f"{self.base_url}/v3/company/{self.realm_id}/query?minorversion=75"
        query = f"SELECT * FROM Customer WHERE DisplayName = '{full_name}'"
        response = self._make_authenticated_request("POST", url, data=query, headers={"Content-Type": "application/text"})

        if response.status_code == 200:
            customers = response.json().get("QueryResponse", {}).get("Customer", [])
            return customers[0] if customers else None
        else:
            raise Exception(f"Error fetching customer: {response.status_code} - {response.text}")


    def create_guest_customer(self, display_name: str = "Guest Customer"):
        # First, check if a customer with this name already exists
        existing = self.find_customer_by_name(display_name)
        if existing:
            return existing  # Return the existing guest customer

        # If not found, create a new one
        url = f"{self.base_url}/v3/company/{self.realm_id}/customer?minorversion=75"
        payload = {
            "DisplayName": display_name,
            "GivenName": "Guest",
            "FamilyName": "Customer"
        }
        headers = {"Content-Type": "application/json"}
        response = self._make_authenticated_request("POST", url, json=payload, headers=headers)

        if response.status_code == 200:
            return response.json()["Customer"]
        else:
            raise Exception(f"Error creating guest: {response.status_code} - {response.text}")



    def rename_customer(self, customer_id: str, new_name: str):
        # Check if the new name already exists to avoid duplication
        if self.find_customer_by_name(new_name):
            raise Exception(f"Customer with name '{new_name}' already exists.")

        # Fetch and update
        url = f"{self.base_url}/v3/company/{self.realm_id}/customer/{customer_id}?minorversion=75"
        existing = self._make_authenticated_request("GET", url).json()["Customer"]

        existing["DisplayName"] = new_name
        update_url = f"{self.base_url}/v3/company/{self.realm_id}/customer?minorversion=75"
        headers = {"Content-Type": "application/json"}
        response = self._make_authenticated_request("POST", update_url, json=existing, headers=headers)

        if response.status_code == 200:
            return response.json()["Customer"]
        else:
            raise Exception(f"Error renaming customer: {response.status_code} - {response.text}")

        
    '''def create_customer(self, display_name):
        # Check if customer already exists
        existing = self.find_customer_by_name(display_name)
        if existing:
            return existing

        url = f"{self.base_url}/v3/company/{self.realm_id}/customer?minorversion=75"
        body = {
            "DisplayName": display_name,
            "FullyQualifiedName": display_name
        }
        headers = {"Content-Type": "application/json"}

        response = self._make_authenticated_request("POST", url, json=body, headers=headers)

        if response.status_code == 200:
            return response.json()["Customer"]
        else:
            raise Exception(f"QuickBooks Error: {response.status_code} - {response.text}")'''


