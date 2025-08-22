import os
import logging
import sys
from typing import List
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from state.session import get_websocket
import stripe
from state.session import set_stripe_order_id, set_paypal_order_id

import paypalrestsdk

logger = logging.getLogger(__name__)

try:
    paypalrestsdk.configure({
        "mode": os.getenv("PAYPAL_MODE", "sandbox"),  # "sandbox" or "live"
        "client_id": os.getenv("PAYPAL_CLIENT_ID"),
        "client_secret": os.getenv("PAYPAL_CLIENT_SECRET")
    })
    logger.info("PayPal SDK configured successfully.")
except Exception as e:
    logger.error(f"Error configuring PayPal SDK: {e}", exc_info=True)

# --- Environment Setup ---
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# --- Pydantic Models ---
class CartItem(BaseModel):
    name: str = Field(..., description="The full name of the product.")
    quantity: int = Field(..., description="How many units of the product are in the cart.")
    price: float = Field(..., description="The price for a single unit of the product.")

class TriggerPaymentArgs(BaseModel):
    cart_items: List[CartItem] = Field(..., description="A complete list of items to be purchased.")
    session_id: str = Field(..., description="Session ID.")

@tool(args_schema=TriggerPaymentArgs)
async def trigger_payment(cart_items: List[CartItem], session_id: str):
    """
    Creates a Stripe PaymentIntent and sends its client_secret to the user's
    WebSocket to initialize an embedded payment form.
    """
    logger.info(f"Attempting to create PaymentIntent for session_id: {session_id}")

    if not stripe.api_key:
        logger.error("Stripe API key is not configured.")
        return "Error: Payment processor is not configured. Please set the STRIPE_API_KEY environment variable."

    ws = get_websocket(session_id)
    if not ws:
        logger.warning(f"No active WebSocket for session {session_id}.")
        return "Something went wrong. No active WebSocket for this session."

    try:
        # Format line items for the Checkout Session API
        line_items = []
        for item in cart_items:
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item.name,
                    },
                    'unit_amount': int(item.price * 100),
                },
                'quantity': item.quantity,
            })
        
        logger.info(f"Line items for Stripe checkout: {line_items}")

        checkout_session = stripe.checkout.Session.create(
            line_items=line_items,
            mode='payment',
            ui_mode='embedded',
            billing_address_collection='required',
            redirect_on_completion='never'
        )
        
        logger.info(f"Stripe Checkout Session created with ID: {checkout_session.id}")
        set_stripe_order_id(session_id, checkout_session.id) # Save the Stripe checkout order ID for later
        
        logger.info(f"Stripe Checkout Session URL: {checkout_session.url}")
        
        message = {
            "type": "payment_intent_created",
            "client_secret": checkout_session.client_secret,
        }
        await ws.send_json(message)
        logger.info(f"Sent payment intent client_secret to WebSocket for session: {session_id}")

        # The tool returns a confirmation that the payment process has been initiated.
        return "Payment form initialized. Let the user know, 'The payment form has been initialized.' DO NOT ask customer to let you know once they are finished paying"

    except Exception as e:
        logger.error(f"Failed to create Stripe PaymentIntent: {e}", exc_info=True)
        return f"Error: Could not create a payment session. Details: {e}"


trigger_payment_tool = trigger_payment