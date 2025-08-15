import os
import logging
import sys
from typing import List
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from backend.state.session import get_websocket
import stripe

# --- Environment Setup ---
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
)

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
    logging.info(f"Attempting to create PaymentIntent for session_id: {session_id}")

    if not stripe.api_key:
        logging.error("Stripe API key is not configured.")
        return "Error: Payment processor is not configured. Please set the STRIPE_API_KEY environment variable."

    ws = get_websocket(session_id)
    if not ws:
        logging.warning(f"No active WebSocket for session {session_id}.")
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
            # logging.info(f"Line items: {}")
            
        
        logging.info(f"Line items: {line_items}")

        checkout_session = stripe.checkout.Session.create(
            line_items=line_items,
            mode='payment',
            ui_mode='embedded',
            billing_address_collection='auto',
            # Return_url for post-payment redirects
            return_url=f'http://localhost:8080'
        )
        
        logging.info(f"Stripe Checkout Session created: {checkout_session.id}")

        message = {
            "type": "payment_intent_created",
            "client_secret": checkout_session.client_secret
        }
        await ws.send_json(message)

        # The tool returns a confirmation that the payment process has been initiated.
        return f"Payment form initialized for session {session_id}. User should now see the form to complete payment."

    except Exception as e:
        logging.error(f"Failed to create Stripe PaymentIntent: {e}")
        return f"Error: Could not create a payment session. Details: {e}"


trigger_payment_tool = trigger_payment