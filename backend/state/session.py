import logging
from typing import Dict
from fastapi import WebSocket
from state.chat_state import ChatState

logger = logging.getLogger(__name__)

session_state: Dict[str, ChatState] = {} 

### State ###

def get_state(session_id: str) -> ChatState:
    logger.debug(f"Attempting to get state for session_id: {session_id}")
    if session_id not in session_state:
        logger.info(f"State not found for session_id: {session_id}. Creating new state.")
        session_state[session_id] = ChatState()
    return session_state[session_id]

def save_state(session_id:str, state: ChatState) -> None:
    logger.debug(f"Saving state for session_id: {session_id}")
    session_state[session_id] = state
    

### Customer ###

def set_customer(session_id: str, customer_id: str | None, *, is_guest: bool | None = None) -> None:
    logger.info(f"Setting customer for session_id: {session_id} to customer_id: {customer_id}")
    s = get_state(session_id)
    s.customer_id = customer_id
    if is_guest is not None:
        s.is_guest = is_guest
        logger.debug(f"Is guest flag set to: {is_guest}")
    save_state(session_id, s)
    
def get_customer(session_id: str):
    logger.debug(f"Getting customer_id for session_id: {session_id}")
    customer = get_state(session_id).customer_id
    logger.debug(f"Found customer_id: {customer}")
    return customer

def mark_guest(session_id: str) -> None:
    logger.info(f"Marking session_id: {session_id} as a guest.")
    s = get_state(session_id)
    s.is_guest = True
    save_state(session_id, s)

def promote_to_real(session_id: str) -> None:
    logger.info(f"Promoting session_id: {session_id} from guest to real customer.")
    s = get_state(session_id)
    s.is_guest = False
    save_state(session_id, s)


### Cart ###

def get_cart(session_id: str):
    logger.debug(f"Getting cart for session_id: {session_id}")
    return get_state(session_id).cart

def add_to_cart(session_id: str, item_name: str, quantity: int):
    logger.info(f"Adding {quantity} of '{item_name}' to cart for session_id: {session_id}")
    cart = get_state(session_id).cart
    try:
        if item_name not in cart:
            cart[item_name] = 0
            logger.debug(f"Item '{item_name}' not in cart. Initializing quantity to 0.")
        cart[item_name] += quantity
        logger.info(f"Successfully added '{item_name}'. New quantity is: {cart[item_name]}")
    except Exception as e:
        logger.error(f"Failed to add '{item_name}' to cart: {e}", exc_info=True)
    
def remove_x_from_cart(session_id: str, item_name: str, quantity: int):
    logger.info(f"Removing {quantity} of '{item_name}' from cart for session_id: {session_id}")
    cart = get_state(session_id).cart
    try:
        if item_name in cart:
            cart[item_name] -= quantity
            logger.info(f"Successfully removed '{quantity}' of '{item_name}'. New quantity: {cart[item_name]}")
            if cart[item_name] <= 0:
                del cart[item_name]
                logger.info(f"Item '{item_name}' quantity reached zero or less. Removing from cart.")
        else:
            logger.warning(f"Attempted to remove '{item_name}', but it was not found in cart.")
    except Exception as e:
        logger.error(f"Failed to remove '{item_name}' from cart: {e}", exc_info=True)

def remove_completely_from_cart(session_id: str, item_name: str):
    logger.info(f"Removing '{item_name}' completely from cart for session_id: {session_id}")
    cart = get_state(session_id).cart
    try:
        if item_name in cart:
            del cart[item_name]
            logger.info(f"Successfully removed '{item_name}' completely from cart.")
        else:
            logger.warning(f"Attempted to remove '{item_name}', but it was not found in cart.")
    except Exception as e:
        logger.error(f"Failed to completely remove '{item_name}' from cart: {e}", exc_info=True)
    

### WebSocket ###

def set_websocket(session_id: str, ws: WebSocket):
    logger.info(f"Setting websocket connection for session_id: {session_id}")
    s = get_state(session_id)
    s.websocket = ws
    save_state(session_id, s)

def get_websocket(session_id:str):
    logger.debug(f"Getting websocket for session_id: {session_id}")
    return get_state(session_id).websocket


### Stripe Order ###

def set_stripe_order_id(session_id: str, stripe_order_id: str):
    logger.info(f"Setting Stripe order ID for session_id: {session_id} to {stripe_order_id}")
    s = get_state(session_id)
    s.stripe_order_id = stripe_order_id 
    save_state(session_id, s)

def get_stripe_order_id(session_id:str):
    logger.debug(f"Getting Stripe order ID for session_id: {session_id}")
    order_id = get_state(session_id).stripe_order_id
    logger.debug(f"Found Stripe order ID: {order_id}")
    return order_id

### PayPal Order ###

def set_paypal_order_id(session_id: str, paypal_order_id: str):
    logger.info(f"Setting PayPal order ID for session_id: {session_id} to {paypal_order_id}")
    s = get_state(session_id)
    s.paypal_order_id = paypal_order_id 
    save_state(session_id, s)

def get_paypal_order_id(session_id:str):
    logger.debug(f"Getting PayPal order ID for session_id: {session_id}")
    order_id = get_state(session_id).paypal_order_id
    logger.debug(f"Found PayPal order ID: {order_id}")
    return order_id