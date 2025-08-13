# tools/quickbooks/quickbooks_wrapper.py

from __future__ import annotations
import os, json, time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from backend.token_service import get_token_for_provider, refresh_token_for_provider

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
        self.base_url = "https://sandbox-quickbooks.api.intuit.com"
        self.minor_version = os.getenv("QB_MINOR_VERSION", "75")
        self.realm_id = os.getenv("QB_REALM_ID")
        if not self.realm_id:
            raise RuntimeError("Missing QB_REALM_ID in environment.")
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.access_expires_at: Optional[int] = None

    # ── token plumbing ─────────────────────────────────────────────────────
    def _load_from_store(self) -> None:
        data = get_token_for_provider("quickbooks")
        if not data:
            raise RuntimeError(
                "QuickBooks tokens not set. Open the authorize URL from "
                "`GET /api/token/quickbooks/authorize`, sign in to sandbox, then POST the code to "
                "`/api/token/quickbooks/exchange`."
            )
        self.access_token = data.get("access_token")
        self.refresh_token = data.get("refresh_token")
        self.access_expires_at = data.get("access_expires_at")

    def _ensure_fresh_access(self) -> None:
        if not self.access_token:
            self._load_from_store()
        # refresh when < 2 minutes remaining
        if not self.access_expires_at or (self.access_expires_at - int(time.time()) <= 120):
            data = refresh_token_for_provider("quickbooks")
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            self.access_expires_at = data.get("access_expires_at")

    # ── http with auto-refresh on 401 as safety net ────────────────────────
    def _make_authenticated_request(self, method: str, url: str, **kwargs) -> requests.Response:
        self._ensure_fresh_access()
        headers = dict(kwargs.pop("headers", {}) or {})
        headers.setdefault("Accept", "application/json")
        headers["Authorization"] = f"Bearer {self.access_token}"
        kwargs["headers"] = headers

        resp = requests.request(method.upper(), url, timeout=20, **kwargs)
        if resp.status_code == 401:
            # try one forced refresh + retry
            self._load_from_store()
            data = refresh_token_for_provider("quickbooks")
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            self.access_expires_at = data.get("access_expires_at")
            headers["Authorization"] = f"Bearer {self.access_token}"
            kwargs["headers"] = headers
            resp = requests.request(method.upper(), url, timeout=20, **kwargs)
        return resp

    # ── public API ─────────────────────────────────────────────────────────
    def create_invoice(self, customer_id: str, line_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not customer_id:
            raise ValueError("customer_id is required.")
        if not line_items:
            raise ValueError("line_items must be a non-empty list.")
        url = f"{self.base_url}/v3/company/{self.realm_id}/invoice"
        params = {"minorversion": self.minor_version}
        body = {"Line": line_items, "CustomerRef": {"value": str(customer_id)}}
        headers = {"Content-Type": "application/json"}
        resp = self._make_authenticated_request("POST", url, params=params, json=body, headers=headers)
        try:
            data = resp.json()
        except Exception:
            raise RuntimeError(f"QuickBooks create_invoice failed: HTTP {resp.status_code} - {resp.text}")
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"QuickBooks create_invoice error: HTTP {resp.status_code} - {json.dumps(data)}")
        return data

    def get_invoice_pdf(self, invoice_id: str) -> bytes:
        if not invoice_id:
            raise ValueError("invoice_id is required.")
        url = f"{self.base_url}/v3/company/{self.realm_id}/invoice/{invoice_id}/pdf"
        headers = {"Accept": "application/pdf"}
        resp = self._make_authenticated_request("GET", url, headers=headers)
        if resp.status_code == 200 and (resp.headers.get("Content-Type","").lower().startswith("application/pdf")):
            return resp.content
        try:
            err = resp.json()
            raise RuntimeError(f"QuickBooks get_invoice_pdf error: HTTP {resp.status_code} - {json.dumps(err)}")
        except ValueError:
            raise RuntimeError(f"QuickBooks get_invoice_pdf failed: HTTP {resp.status_code} - {resp.text}")


    # ──────────────────────────────────────────────────────────────────────
    # Customer helpers
    # ──────────────────────────────────────────────────────────────────────
    @staticmethod
    def _escape_qbo_literal(s: str) -> str:
        """Escape single quotes in QBO SQL literals ('' inside string)."""
        return s.replace("'", "''")

    def find_customer_by_name(self, display_name: str) -> Optional[Dict[str, Any]]:
        """Exact match by DisplayName using documented GET /query."""
        safe = self._escape_qbo_literal((display_name or "").strip())
        if not safe:
            return None

        q = f"SELECT * FROM Customer WHERE DisplayName = '{safe}'"
        url = f"{self.base_url}/v3/company/{self.realm_id}/query"
        params = {"query": q, "minorversion": self.minor_version}

        resp = self._make_authenticated_request("GET", url, params=params)
        if resp.status_code != 200:
            raise RuntimeError(f"Customer query failed: HTTP {resp.status_code} - {resp.text}")

        data = resp.json() or {}
        customers = (data.get("QueryResponse") or {}).get("Customer", [])
        return customers[0] if customers else None

    def find_customer_like(self, name_fragment: str) -> List[Dict[str, Any]]:
        """LIKE search helper (useful for fuzzy lookups)."""
        safe = self._escape_qbo_literal((name_fragment or "").strip())
        if not safe:
            return []

        q = f"SELECT Id, DisplayName FROM Customer WHERE DisplayName LIKE '%{safe}%' ORDER BY MetaData.CreateTime DESC"
        url = f"{self.base_url}/v3/company/{self.realm_id}/query"
        params = {"query": q, "minorversion": self.minor_version}

        resp = self._make_authenticated_request("GET", url, params=params)
        if resp.status_code != 200:
            raise RuntimeError(f"Customer LIKE query failed: HTTP {resp.status_code} - {resp.text}")

        data = resp.json() or {}
        return (data.get("QueryResponse") or {}).get("Customer", []) or []

    def create_guest_customer(self, display_name: str = "Guest Customer") -> Dict[str, Any]:
        """Idempotent: returns existing if DisplayName already present."""
        existing = self.find_customer_by_name(display_name)
        if existing:
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
            return resp.json()["Customer"]

        raise RuntimeError(f"Error creating guest: HTTP {resp.status_code} - {resp.text}")

    def create_customer(
        self,
        display_name: str,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        address: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a full (non‑guest) customer.
        If DisplayName exists, returns the existing record.
        """
        display_name = (display_name or "").strip()
        if not display_name:
            raise ValueError("display_name is required")

        existing = self.find_customer_by_name(display_name)
        if existing:
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

        url = f"{self.base_url}/v3/company/{self.realm_id}/customer"
        params = {"minorversion": self.minor_version}
        headers = {"Content-Type": "application/json"}

        resp = self._make_authenticated_request("POST", url, params=params, json=payload, headers=headers)
        if resp.status_code == 200:
            return resp.json()["Customer"]

        raise RuntimeError(f"QuickBooks create_customer failed: HTTP {resp.status_code} - {resp.text}")

    def rename_customer(
        self,
        customer_id: str,
        new_name: str,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        address: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Sparse update of Customer (requires current SyncToken).
        Fails early if another customer already has `new_name`.
        """
        new_name = (new_name or "").strip()
        if not new_name:
            raise ValueError("new_name is required")

        # prevent duplicates
        if self.find_customer_by_name(new_name):
            raise RuntimeError(f"Customer with name '{new_name}' already exists.")

        # fetch current to obtain SyncToken
        get_url = f"{self.base_url}/v3/company/{self.realm_id}/customer/{customer_id}"
        get_params = {"minorversion": self.minor_version}
        get_resp = self._make_authenticated_request("GET", get_url, params=get_params)
        if get_resp.status_code != 200:
            raise RuntimeError(f"Fetch customer failed: HTTP {get_resp.status_code} - {get_resp.text}")

        current = get_resp.json().get("Customer", {})
        sync_token = current.get("SyncToken")
        if sync_token is None:
            raise RuntimeError("Missing SyncToken for customer update.")

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

        update_url = f"{self.base_url}/v3/company/{self.realm_id}/customer"
        update_params = {"minorversion": self.minor_version}
        headers = {"Content-Type": "application/json"}

        upd_resp = self._make_authenticated_request(
            "POST", update_url, params=update_params, json=update_payload, headers=headers
        )
        if upd_resp.status_code == 200:
            return upd_resp.json()["Customer"]

        raise RuntimeError(f"Error renaming customer: HTTP {upd_resp.status_code} - {upd_resp.text}")
