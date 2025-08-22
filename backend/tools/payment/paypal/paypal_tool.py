import os
import json
import requests
from typing import Optional
from pathlib import Path
import logging

from langchain.agents import Tool
from langchain_core.tools import tool
from dotenv import load_dotenv

from state.session import set_paypal_order_id, get_paypal_order_id
from token_service import get_token_for_provider, refresh_token_for_provider
from paypal_agent_toolkit.langchain.toolkit import PayPalToolkit
from paypal_agent_toolkit.shared.configuration import Configuration, Context

logger = logging.getLogger(__name__)

load_dotenv()

# ----------------------------
# PayPal Toolkit (LangChain) 
# ----------------------------
def get_paypal_tools() -> list[Tool]:
    paypal_client_id = os.getenv("PAYPAL_CLIENT_ID")
    paypal_client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
    if not paypal_client_id or not paypal_client_secret:
        logger.error("PayPal client ID and secret must be set in environment variables.")
        raise ValueError("PayPal client ID and secret must be set in environment variables.")

    configuration = Configuration(
        actions={
            "orders": {"create": True, "get": True, "capture": True},
            # enable invoices if/when needed
            # "invoices": {"create": True, "list": True, "send": True},
        },
        context=Context(sandbox=True)
    )

    toolkit = PayPalToolkit(
        client_id=paypal_client_id,
        secret=paypal_client_secret,
        configuration=configuration
    )
    logger.info("PayPal Toolkit initialized.")
    return toolkit.get_tools()

# ----------------------------
# Token-aware HTTP helper
# ----------------------------
def _request_with_auto_refresh(method, url, headers=None, **kwargs):
    provider = "paypal"
    hdrs = dict(headers or {})
    tok = get_token_for_provider(provider)
    if tok and isinstance(tok, dict) and tok.get("access_token"):
        hdrs.setdefault("Authorization", f"Bearer {tok['access_token']}")
    
    logger.debug(f"Making {method} request to {url}")
    resp = requests.request(method.upper(), url, headers=hdrs, **kwargs)
    
    if getattr(resp, "status_code", None) in (401, 403):
        logger.warning(f"Request to {url} failed with status {resp.status_code}. Attempting token refresh.")
        try:
            new_tok = refresh_token_for_provider(provider)
            if new_tok and new_tok.get("access_token"):
                hdrs["Authorization"] = f"Bearer {new_tok['access_token']}"
                resp = requests.request(method.upper(), url, headers=hdrs, **kwargs)
                logger.info("Token refreshed and request retried successfully.")
            else:
                logger.error("Failed to get a new access token during refresh.")
        except Exception as e:
            logger.error(f"An exception occurred during token refresh: {e}", exc_info=True)
    return resp

# ----------------------------
# Env / base URL
# ----------------------------
PAYPAL_ENV = os.getenv("PAYPAL_ENV", "sandbox").lower()  # "sandbox" or "live"
def _paypal_api_base() -> str:
    return "https://api-m.paypal.com" if PAYPAL_ENV == "live" else "https://api-m.sandbox.paypal.com"

# ----------------------------
# Order ID persistence
# ----------------------------
_ORDER_FILE = Path(__file__).parent / "last_order_id.txt"

def _write_order_id(oid: str) -> None:
    try:
        _ORDER_FILE.write_text(oid.strip(), encoding="utf-8")
        logger.info(f"PayPal order ID '{oid}' written to file.")
    except Exception as e:
        logger.error(f"Failed to write PayPal order ID to file: {e}", exc_info=True)

def _read_order_id() -> Optional[str]:
    try:
        if _ORDER_FILE.exists():
            oid = _ORDER_FILE.read_text(encoding="utf-8").strip()
            logger.info(f"Read PayPal order ID '{oid}' from file.")
            return oid
    except Exception as e:
        logger.error(f"Failed to read PayPal order ID from file: {e}", exc_info=True)
    logger.info("No PayPal order ID found in file.")
    return None

def create_paypal_order(
    amount: float,
    currency: str = "USD",
    description: str = "Chai Order",
    return_url: Optional[str] = None,
    cancel_url: Optional[str] = None,
) -> dict:
    """Create a PayPal order (intent=CAPTURE) and return the JSON response."""
    logger.info(f"Attempting to create PayPal order for amount {amount} {currency}.")
    url = f"{_paypal_api_base()}/v2/checkout/orders"
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "description": description,
            "amount": {"currency_code": currency, "value": f"{amount:.2f}"}
        }],
    }
    if return_url and cancel_url:
        payload["application_context"] = {"return_url": return_url, "cancel_url": cancel_url}
        
    logger.debug(f"Payload for PayPal order: {payload}")
    resp = _request_with_auto_refresh("POST", url, headers={"Content-Type": "application/json"}, json=payload)
    
    try:
        data = resp.json()
    except Exception:
        logger.error(f"PayPal create order failed: HTTP {resp.status_code} - Invalid JSON response: {resp.text}", exc_info=True)
        raise RuntimeError(f"PayPal create order failed: HTTP {resp.status_code} - {resp.text}")

    if not resp.ok:
        logger.error(f"PayPal create order error: HTTP {resp.status_code} - Response: {json.dumps(data)}")
        raise RuntimeError(f"PayPal create order error: HTTP {resp.status_code} - {json.dumps(data)}")

    oid = data.get("id")
    if oid:
        _write_order_id(oid)
        logger.info(f"PayPal order created with ID: {oid}")
    else:
        logger.warning(f"PayPal order created but ID not found in response: {data}")
    return data

def capture_paypal_order(order_id: Optional[str] = None) -> dict:
    """Capture an existing PayPal order by ID."""
    oid = order_id or _read_order_id()
    if not oid or str(oid).lower().startswith("no valid paypal"):
        logger.error("No valid PayPal order_id provided or saved.")
        raise ValueError("No valid PayPal order_id provided or saved.")

    logger.info(f"Attempting to capture PayPal order with ID: {oid}")
    url = f"{_paypal_api_base()}/v2/checkout/orders/{oid}/capture"
    resp = _request_with_auto_refresh("POST", url, headers={"Content-Type": "application/json"})
    
    try:
        data = resp.json()
    except Exception:
        logger.error(f"PayPal capture failed: HTTP {resp.status_code} - Invalid JSON response: {resp.text}", exc_info=True)
        raise RuntimeError(f"PayPal capture failed: HTTP {resp.status_code} - {resp.text}")

    if not resp.ok:
        logger.error(f"PayPal capture error: HTTP {resp.status_code} - Response: {json.dumps(data)}")
        raise RuntimeError(f"PayPal capture error: HTTP {resp.status_code} - {json.dumps(data)}")
    
    logger.info(f"PayPal order with ID {oid} captured successfully.")
    return data

# ----------------------------
# Agent-facing LangChain tools
# (optional, if your agent wants to call them)
# ----------------------------

@tool
def save_order_id_tool(session_id: str, order_id: str) -> str:
    """
    Saves the provided PayPal order ID to a global variable for later use.
    This is useful for persisting the order ID between different agent steps or calls.
    
    Args:
        new_order_id (str): The PayPal order ID to save.
        
    Returns:
        str: A confirmation message indicating the order ID has been saved.
    """
    logger.info(f"Tool 'save_order_id_tool' called for session '{session_id}' with order ID: {order_id}")
    set_paypal_order_id(session_id, order_id)
    logger.info(f"PayPal order ID '{order_id}' saved to session state.")
    return f"Order ID '{order_id}' has been saved successfully."

@tool("get_order_id_tool")
def get_order_id_tool(session_id: str) -> dict:
    """
    Return the saved PayPal order id.
    Output shape:
      {"exists": true, "order_id": "XYZ"}  OR  {"exists": false, "order_id": null}
    Never return prose.
    """
    logger.info(f"Tool 'get_order_id_tool' called for session '{session_id}'")
    oid = get_paypal_order_id(session_id)
    if oid:
        logger.info(f"Found PayPal order ID '{oid}' for session '{session_id}'.")
        return {"exists": True, "order_id": oid}
    else:
        logger.info(f"No PayPal order ID found for session '{session_id}'.")
        return {"exists": False, "order_id": None}

# For convenience if you want to register tools list elsewhere
order_tools = [save_order_id_tool, get_order_id_tool]

# Explicit exports
__all__ = [
    "get_paypal_tools",
    "create_paypal_order",
    "capture_paypal_order",
    "save_order_id_tool",
    "get_order_id_tool",
    "order_tools",
]