# tools/quickbooks/quickbooks_wrapper.py

from __future__ import annotations
import os, json, time
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

import requests
from dotenv import load_dotenv
from token_service import get_token_for_provider, refresh_token_for_provider

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH if ENV_PATH.exists() else None)

class QuickBooksWrapper:
    """
    Wrapper with lazy token load + proactive refresh.
    - No crash if tokens are missing; raises clear, actionable error.
    - Auto-refreshes if `access_expires_at` is near/over.
    """

    def __init__(self) -> None:
        logger.info("Initializing QuickBooksWrapper.")
        self.base_url = "https://sandbox-quickbooks.api.intuit.com"
        self.minor_version = os.getenv("QB_MINOR_VERSION", "75")
        self.realm_id = os.getenv("QB_REALM_ID")
        if not self.realm_id:
            logger.critical("Missing QB_REALM_ID in environment.")
            raise RuntimeError("Missing QB_REALM_ID in environment.")
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.access_expires_at: Optional[int] = None
        logger.debug(f"QuickBooksWrapper initialized with base_url: {self.base_url}")

    # ── token plumbing ─────────────────────────────────────────────────────
    def _load_from_store(self) -> None:
        logger.info("Attempting to load QuickBooks tokens from store.")
        data = get_token_for_provider("quickbooks")
        if not data:
            logger.error("QuickBooks tokens not found in store.")
            raise RuntimeError(
                "QuickBooks tokens not set. Open the authorize URL from "
                "`GET /api/token/quickbooks/authorize`, sign in to sandbox, then POST the code to "
                "`/api/token/quickbooks/exchange`."
            )
        self.access_token = data.get("access_token")
        self.refresh_token = data.get("refresh_token")
        self.access_expires_at = data.get("access_expires_at")
        logger.info("QuickBooks tokens loaded successfully.")

    def _ensure_fresh_access(self) -> None:
        logger.debug("Ensuring fresh QuickBooks access token.")
        if not self.access_token:
            self._load_from_store()
        # refresh when < 2 minutes remaining
        if not self.access_expires_at or (self.access_expires_at - int(time.time()) <= 120):
            logger.info("Access token is near expiration or missing. Refreshing token.")
            data = refresh_token_for_provider("quickbooks")
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            self.access_expires_at = data.get("access_expires_at")
            logger.info("Token refreshed successfully.")

    # ── http with auto-refresh on 401 as safety net ────────────────────────
    def _make_authenticated_request(self, method: str, url: str, **kwargs) -> requests.Response:
        self._ensure_fresh_access()
        headers = dict(kwargs.pop("headers", {}) or {})
        headers.setdefault("Accept", "application/json")
        headers["Authorization"] = f"Bearer {self.access_token}"
        kwargs["headers"] = headers

        logger.debug(f"Making authenticated {method} request to {url}")
        resp = requests.request(method.upper(), url, timeout=20, **kwargs)
        
        if resp.status_code == 401:
            logger.warning("Request failed with 401 Unauthorized. Attempting token refresh and retry.")
            try:
                self._load_from_store()
                data = refresh_token_for_provider("quickbooks")
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                self.access_expires_at = data.get("access_expires_at")
                headers["Authorization"] = f"Bearer {self.access_token}"
                kwargs["headers"] = headers
                resp = requests.request(method.upper(), url, timeout=20, **kwargs)
                logger.info("Token refresh and retry successful.")
            except Exception as e:
                logger.error(f"Token refresh failed during 401 retry: {e}", exc_info=True)
                raise RuntimeError(f"Failed to refresh token: {e}")
        
        logger.debug(f"Request to {url} completed with status code: {resp.status_code}")
        return resp

    # ── public API ─────────────────────────────────────────────────────────
    def create_invoice(self, customer_id: str, line_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.info(f"Creating invoice for customer_id: {customer_id}")
        if not customer_id:
            logger.error("customer_id is required but was not provided.")
            raise ValueError("customer_id is required.")
        if not line_items:
            logger.error("line_items must be a non-empty list.")
            raise ValueError("line_items must be a non-empty list.")
        
        url = f"{self.base_url}/v3/company/{self.realm_id}/invoice"
        params = {"minorversion": self.minor_version}
        body = {"Line": line_items, "CustomerRef": {"value": str(customer_id)}}
        headers = {"Content-Type": "application/json"}
        
        resp = self._make_authenticated_request("POST", url, params=params, json=body, headers=headers)
        
        try:
            data = resp.json()
        except json.JSONDecodeError:
            logger.error(f"QuickBooks create_invoice failed: HTTP {resp.status_code} - Invalid JSON response: {resp.text}")
            raise RuntimeError(f"QuickBooks create_invoice failed: HTTP {resp.status_code} - {resp.text}")
        
        if resp.status_code not in (200, 201):
            logger.error(f"QuickBooks create_invoice error: HTTP {resp.status_code} - Response: {json.dumps(data)}")
            raise RuntimeError(f"QuickBooks create_invoice error: HTTP {resp.status_code} - {json.dumps(data)}")
            
        logger.info("Invoice created successfully.")
        return data

    def get_invoice_pdf(self, invoice_id: str) -> bytes:
        logger.info(f"Getting PDF for invoice_id: {invoice_id}")
        if not invoice_id:
            logger.error("invoice_id is required but was not provided.")
            raise ValueError("invoice_id is required.")
            
        url = f"{self.base_url}/v3/company/{self.realm_id}/invoice/{invoice_id}/pdf"
        headers = {"Accept": "application/pdf"}
        resp = self._make_authenticated_request("GET", url, headers=headers)
        
        if resp.status_code == 200 and (resp.headers.get("Content-Type","").lower().startswith("application/pdf")):
            logger.info("Successfully retrieved invoice PDF.")
            return resp.content
        
        try:
            err = resp.json()
            logger.error(f"QuickBooks get_invoice_pdf error: HTTP {resp.status_code} - Response: {json.dumps(err)}")
            raise RuntimeError(f"QuickBooks get_invoice_pdf error: HTTP {resp.status_code} - {json.dumps(err)}")
        except ValueError:
            logger.error(f"QuickBooks get_invoice_pdf failed: HTTP {resp.status_code} - Non-JSON response: {resp.text}")
            raise RuntimeError(f"QuickBooks get_invoice_pdf failed: HTTP {resp.status_code} - {resp.text}")

    # ──────────────────────────────────────────────────────────────────────
    # Customer helpers
    # ──────────────────────────────────────────────────────────────────────
    @staticmethod
    def _escape_qbo_literal(s: str) -> str:
        """Escape single quotes in QBO SQL literals ('' inside string)."""
        return s.replace("'", "''")

    def find_customer_by_name(self, display_name: str) -> Optional[Dict[str, Any]]:
        logger.info(f"Searching for customer by name: {display_name}")
        safe = self._escape_qbo_literal((display_name or "").strip())
        if not safe:
            logger.warning("Display name is empty. Cannot search for customer.")
            return None

        q = f"SELECT * FROM Customer WHERE DisplayName = '{safe}'"
        url = f"{self.base_url}/v3/company/{self.realm_id}/query"
        params = {"query": q, "minorversion": self.minor_version}

        resp = self._make_authenticated_request("GET", url, params=params)
        if resp.status_code != 200:
            logger.error(f"Customer query failed: HTTP {resp.status_code} - {resp.text}")
            raise RuntimeError(f"Customer query failed: HTTP {resp.status_code} - {resp.text}")

        data = resp.json() or {}
        customers = (data.get("QueryResponse") or {}).get("Customer", [])
        if customers:
            logger.info(f"Found customer with name '{display_name}'.")
            return customers[0]
        else:
            logger.info(f"No customer found with exact name '{display_name}'.")
            return None

    def find_customer_like(self, name_fragment: str) -> List[Dict[str, Any]]:
        logger.info(f"Searching for customers with name fragment: {name_fragment}")
        safe = self._escape_qbo_literal((name_fragment or "").strip())
        if not safe:
            logger.warning("Name fragment is empty. Returning empty list.")
            return []

        q = f"SELECT Id, DisplayName FROM Customer WHERE DisplayName LIKE '%{safe}%' ORDER BY MetaData.CreateTime DESC"
        url = f"{self.base_url}/v3/company/{self.realm_id}/query"
        params = {"query": q, "minorversion": self.minor_version}

        resp = self._make_authenticated_request("GET", url, params=params)
        if resp.status_code != 200:
            logger.error(f"Customer LIKE query failed: HTTP {resp.status_code} - {resp.text}")
            raise RuntimeError(f"Customer LIKE query failed: HTTP {resp.status_code} - {resp.text}")

        data = resp.json() or {}
        customers = (data.get("QueryResponse") or {}).get("Customer", []) or []
        logger.info(f"Found {len(customers)} customers matching fragment '{name_fragment}'.")
        return customers

    def create_guest_customer(self, display_name: str = "Guest Customer") -> Dict[str, Any]:
        logger.info(f"Creating or retrieving guest customer with display name: {display_name}")
        existing = self.find_customer_by_name(display_name)
        if existing:
            logger.info("Guest customer already exists. Returning existing record.")
            return existing

        url = f"{self.base_url}/v3/company/{self.realm_id}/customer"
        params = {"minorversion": self.minor_version}
        payload = {
            "DisplayName": display_name,
            "GivenName": (display_name.split()[0] if display_name.split() else "Guest"),
            "FamilyName": (display_name.split()[-1] if len(display_name.split()) > 1 else "Customer"),
        }
        headers = {"Content-Type": "application/json"}

        resp = self._make_authenticated_request("POST", url, params=params, json=payload, headers=headers)
        if resp.status_code == 200:
            logger.info(f"Successfully created new guest customer: {resp.json().get('Customer', {}).get('DisplayName')}")
            return resp.json()["Customer"]

        logger.error(f"Error creating guest: HTTP {resp.status_code} - {resp.text}")
        raise RuntimeError(f"Error creating guest: HTTP {resp.status_code} - {resp.text}")

    def create_customer(
        self,
        display_name: str,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        address: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        logger.info(f"Creating or retrieving customer with display name: {display_name}")
        display_name = (display_name or "").strip()
        if not display_name:
            logger.error("display_name is required but was not provided.")
            raise ValueError("display_name is required")

        existing = self.find_customer_by_name(display_name)
        if existing:
            logger.info("Customer already exists. Returning existing record.")
            return existing

        payload: Dict[str, Any] = {
            "DisplayName": display_name,
            "FullyQualifiedName": display_name,
            "GivenName": display_name.split()[0],
            "FamilyName": display_name.split()[-1],
        }
        if phone:
            payload["PrimaryPhone"] = {"FreeFormNumber": phone}
        if email:
            payload["PrimaryEmailAddr"] = {"Address": email}
        if address:
            payload["BillAddr"] = address
            payload["ShipAddr"] = address
        
        logger.debug(f"Payload for new customer creation: {payload}")
        
        url = f"{self.base_url}/v3/company/{self.realm_id}/customer"
        params = {"minorversion": self.minor_version}
        headers = {"Content-Type": "application/json"}

        resp = self._make_authenticated_request("POST", url, params=params, json=payload, headers=headers)
        if resp.status_code == 200:
            logger.info(f"Successfully created new customer: {resp.json().get('Customer', {}).get('DisplayName')}")
            return resp.json()["Customer"]

        logger.error(f"QuickBooks create_customer failed: HTTP {resp.status_code} - {resp.text}")
        raise RuntimeError(f"QuickBooks create_customer failed: HTTP {resp.status_code} - {resp.text}")

    def rename_customer(
        self,
        customer_id: str,
        new_name: str,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        address: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        logger.info(f"Attempting to rename customer with ID: {customer_id} to '{new_name}'")
        new_name = (new_name or "").strip()
        if not new_name:
            logger.error("new_name is required but was not provided.")
            raise ValueError("new_name is required")

        # prevent duplicates
        if self.find_customer_by_name(new_name):
            logger.error(f"Rename failed: a customer with name '{new_name}' already exists.")
            raise RuntimeError(f"Customer with name '{new_name}' already exists.")

        # fetch current to obtain SyncToken
        logger.debug(f"Fetching current customer data for ID: {customer_id}")
        get_url = f"{self.base_url}/v3/company/{self.realm_id}/customer/{customer_id}"
        get_params = {"minorversion": self.minor_version}
        get_resp = self._make_authenticated_request("GET", get_url, params=get_params)
        
        if get_resp.status_code != 200:
            logger.error(f"Fetch customer failed: HTTP {get_resp.status_code} - {get_resp.text}")
            raise RuntimeError(f"Fetch customer failed: HTTP {get_resp.status_code} - {get_resp.text}")

        current = get_resp.json().get("Customer", {})
        sync_token = current.get("SyncToken")
        if sync_token is None:
            logger.error("Missing SyncToken for customer update.")
            raise RuntimeError("Missing SyncToken for customer update.")
        
        logger.info("Successfully fetched SyncToken for update.")

        update_payload: Dict[str, Any] = {
            "Id": customer_id,
            "SyncToken": sync_token,
            "sparse": True,
            "DisplayName": new_name,
            "GivenName": new_name.split()[0],
            "FamilyName": new_name.split()[-1],
        }
        if phone:
            update_payload["PrimaryPhone"] = {"FreeFormNumber": phone}
        if email:
            update_payload["PrimaryEmailAddr"] = {"Address": email}
        if address:
            update_payload["BillAddr"] = address
            update_payload["ShipAddr"] = address
        
        logger.debug(f"Payload for customer rename: {update_payload}")
        
        update_url = f"{self.base_url}/v3/company/{self.realm_id}/customer"
        update_params = {"minorversion": self.minor_version}
        headers = {"Content-Type": "application/json"}

        upd_resp = self._make_authenticated_request(
            "POST", update_url, params=update_params, json=update_payload, headers=headers
        )
        if upd_resp.status_code == 200:
            logger.info(f"Customer with ID {customer_id} successfully renamed to '{new_name}'.")
            return upd_resp.json()["Customer"]

        logger.error(f"Error renaming customer: HTTP {upd_resp.status_code} - {upd_resp.text}")
        raise RuntimeError(f"Error renaming customer: HTTP {upd_resp.status_code} - {upd_resp.text}")