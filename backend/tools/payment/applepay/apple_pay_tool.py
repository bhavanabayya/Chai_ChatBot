import logging
import requests
import os
from langchain_core.tools import tool
from dotenv import load_dotenv
from typing import Optional
from token_service import get_token_for_provider, refresh_token_for_provider

logger = logging.getLogger(__name__)

load_dotenv()

def _request_with_auto_refresh(method, url, headers=None, **kwargs):
    provider = "applepay"
    hdrs = dict(headers or {})
    tok = get_token_for_provider(provider)
    if tok and isinstance(tok, dict) and tok.get("access_token"):
        hdrs.setdefault("Authorization", f"Bearer {tok['access_token']}")
    
    logger.debug(f"Making {method} request to {url}")
    resp = requests.request(method.upper(), url, headers=hdrs, **kwargs)
    
    if getattr(resp, "status_code", None) in (401, 403):
        logger.warning(f"Request failed with status {resp.status_code}. Attempting token refresh.")
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

# Global variable for Apple Pay session ID (consider using a persistent store in production)
apple_pay_session_id = ""

@tool
def generate_apple_pay_link(amount_dollars: float, product_name: str = "Chai Corner Order") -> str:
    """
    Generates an Apple Pay payment link using Stripe Checkout.
    
    Args:
        amount_dollars (float): The payment amount in dollars
        product_name (str): The name of the product/order (default: "Chai Corner Order")
    
    Returns:
        str: Apple Pay payment link or error message
    """
    logger.info(f"Generating Apple Pay link for {product_name} with amount ${amount_dollars}")
    
    try:
        # Try to import stripe dynamically
        import stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        
        if not stripe.api_key:
            logger.warning("Stripe API key not found. Using demo link.")
            return "https://checkout.stripe.com/demo-apple-pay-link"
        
        amount_cents = int(amount_dollars * 100)
        
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": amount_cents,
                    "product_data": {
                        "name": product_name,
                    },
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url="https://lightningminds.com/success",
            cancel_url="https://lightningminds.com/cancel",
        )
        
        # Save session ID globally for potential future use
        global apple_pay_session_id
        apple_pay_session_id = session.id
        logger.info(f"Generated Stripe Checkout Session ID: {session.id}")
        logger.info(f"Apple Pay Link Generated: {session.url}")
        
        # Return just the URL
        return session.url
        
    except ImportError:
        logger.error("Stripe library not available. Using demo link.")
        return "https://checkout.stripe.com/demo-apple-pay-link"
    except Exception as e:
        logger.error(f"Apple Pay Error: {str(e)}", exc_info=True)
        return "https://checkout.stripe.com/demo-apple-pay-link"

@tool
def get_apple_pay_session_status(session_id: Optional[str] = None) -> str:
    """
    Retrieves the status of an Apple Pay (Stripe) checkout session.
    
    Args:
        session_id (str, optional): The Stripe session ID. If not provided, uses the last generated session.
    
    Returns:
        str: Session status information
    """
    logger.info(f"Checking Apple Pay session status for ID: {session_id}")
    try:
        import stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        
        if not stripe.api_key:
            logger.error("Stripe API key not configured.")
            return "Error: Stripe API key not configured."
        
        # Use provided session_id or fall back to global one
        session_to_check = session_id or apple_pay_session_id
        
        if not session_to_check:
            logger.warning("No Apple Pay session ID available. Cannot check status.")
            return "No Apple Pay session ID available. Please generate a payment link first."
        
        session = stripe.checkout.Session.retrieve(session_to_check)
        
        status_info = {
            "id": session.id,
            "status": session.status,
            "payment_status": session.payment_status,
            "amount_total": session.amount_total / 100 if session.amount_total else 0,  # Convert cents to dollars
            "currency": session.currency,
            "url": session.url
        }
        
        logger.info(f"Retrieved session status: {status_info}")
        return f"Apple Pay Session Status: {status_info['status']}, Payment Status: {status_info['payment_status']}, Amount: ${status_info['amount_total']}"
        
    except Exception as e:
        logger.error(f"Error retrieving Apple Pay session status: {str(e)}", exc_info=True)
        return f"Error retrieving Apple Pay session status: {str(e)}"

@tool
def save_apple_pay_session_id(session_id: str) -> str:
    """
    Saves an Apple Pay session ID for later reference.
    
    Args:
        session_id (str): The Stripe session ID to save
    
    Returns:
        str: Confirmation message
    """
    logger.info(f"Saving Apple Pay session ID: {session_id}")
    global apple_pay_session_id
    apple_pay_session_id = session_id
    logger.info(f"Apple Pay session ID '{session_id}' has been saved.")
    return f"Apple Pay session ID '{session_id}' has been saved successfully."

@tool
def get_apple_pay_session_id() -> str:
    """
    Retrieves the currently saved Apple Pay session ID.
    
    Returns:
        str: The saved session ID or a message if none is saved
    """
    logger.info("Attempting to retrieve saved Apple Pay session ID.")
    if apple_pay_session_id:
        logger.info(f"Retrieved saved Apple Pay session ID: {apple_pay_session_id}")
        return apple_pay_session_id
    else:
        logger.warning("No Apple Pay session ID has been saved yet.")
        return "No Apple Pay session ID has been saved yet."

# List of Apple Pay tools to be imported by tool_config
apple_pay_tools = [
    generate_apple_pay_link,
    get_apple_pay_session_status,
    save_apple_pay_session_id,
    get_apple_pay_session_id
]