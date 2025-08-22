import logging
import os
import stripe
from langchain_core.tools import tool
from pydantic import BaseModel
from state.session import get_stripe_order_id

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class CheckoutSessionRequest(BaseModel):
    """Request model for checking a checkout session."""
    session_id: str
    
@tool("stripe_checkout_status_tool", return_direct=True)
def stripe_checkout_status_tool(session_id: str) -> str:
    """
    Checks the status of a Stripe Checkout Session.

    Args:
        session_id: The UUID string of the session of the user. Not the Stripe Session ID.

    Returns:
        A string indicating the status of the checkout session.
    """
    logger.info(f"Tool 'stripe_checkout_status_tool' called for session_id: {session_id}")

    if not stripe.api_key:
        logger.error("Stripe API key is not configured. Returning error.")
        return "Error: Stripe API key is not configured."

    try:
        order_id = get_stripe_order_id(session_id)
        if not order_id:
            logger.warning(f"No Stripe order ID found for session: {session_id}")
            return "No Stripe order ID found for this session."
            
        logger.info(f"Retrieving Stripe Checkout Session for order ID: {order_id}")
        order = stripe.checkout.Session.retrieve(order_id)
        
        payment_status = order.payment_status
        logger.info(f"Successfully retrieved Stripe session. Payment Status: {payment_status}")
        
        return (
            f"Payment Status: {payment_status}."
        )
    except stripe.error.StripeError as e:
        logger.error(f"Stripe API error when retrieving checkout session: {str(e)}", exc_info=True)
        return f"Error retrieving checkout session: {str(e)}"
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {str(e)}", exc_info=True)
        return f"An unexpected error occurred: {str(e)}"