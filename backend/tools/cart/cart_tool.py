import logging
from collections import defaultdict
from langchain_core.tools import tool

# Create a logger for this module
logger = logging.getLogger(__name__)

# This dictionary will store cart objects, with session IDs as keys.
# Structure: { "session_id_1": {"item_1": qty, "item_2": qty}, "session_id_2": ... }
# This is an in-memory store. It will be cleared if the server restarts.
session_carts = {}

def get_cart_for_session(session_id: str) -> defaultdict:
    """Retrieves or creates a cart object for a given session ID."""
    if session_id not in session_carts:
        logger.info(f"Cart not found for session '{session_id}'. Creating a new one.")
        session_carts[session_id] = defaultdict(int)
    return session_carts[session_id]

@tool
def add_to_cart(session_id: str, item_name: str, quantity: int) -> str:
    """
    Adds a specified quantity of an item to the shopping cart.
    """
    logger.info(f"Tool: add_to_cart called for session '{session_id}'. Adding {quantity} of '{item_name}'.")
    
    if quantity <= 0:
        logger.warning(f"Invalid quantity '{quantity}' for adding to cart. Quantity must be positive.")
        return "Quantity must be a positive integer to add to cart."
    
    cart = get_cart_for_session(session_id)
    
    cart[item_name] += quantity
    logger.info(f"Added {quantity} x {item_name} to cart for session '{session_id}'.")
    logger.debug(f"Current cart state for '{session_id}': {dict(cart)}")
    
    return f"Added {quantity} x {item_name} to the cart. Current quantity: {cart[item_name]}."

@tool
def remove_from_cart(session_id: str, item_name: str, quantity: int) -> str:
    """
    Removes a specified quantity of an item from the shopping cart.
    """
    logger.info(f"Tool: remove_from_cart called for session '{session_id}'. Removing {quantity} of '{item_name}'.")

    if quantity <= 0:
        logger.warning(f"Invalid quantity '{quantity}' for removing from cart. Quantity must be positive.")
        return "Quantity must be a positive integer to remove from cart."
    
    cart = get_cart_for_session(session_id)
    
    if item_name not in cart or cart[item_name] == 0:
        logger.warning(f"Attempted to remove '{item_name}' but it was not in the cart for session '{session_id}'.")
        return f"{item_name} is not in the cart."

    current_quantity = cart[item_name]
    if quantity >= current_quantity:
        del cart[item_name]
        logger.info(f"Removed all {current_quantity} x {item_name} from cart for session '{session_id}'.")
        logger.debug(f"Current cart state for '{session_id}': {dict(cart)}")
        return f"Removed all {current_quantity} x {item_name} from the cart."
    else:
        cart[item_name] -= quantity
        logger.info(f"Removed {quantity} x {item_name} from cart for session '{session_id}'.")
        logger.debug(f"Current cart state for '{session_id}': {dict(cart)}")
        return f"Removed {quantity} x {item_name} from the cart. Remaining quantity: {cart[item_name]}."

@tool
def view_cart(session_id: str) -> str:
    """
    Displays the current contents of the shopping cart.
    """
    logger.info(f"Tool: view_cart called for session '{session_id}'.")
    cart = get_cart_for_session(session_id)
    
    if not cart:
        logger.info(f"Cart for session '{session_id}' is empty.")
        return "The cart is currently empty."

    cart_items = [f"{qty} x {item}" for item, qty in cart.items()]
    cart_summary = ", ".join(cart_items)
    logger.info(f"Cart contents for session '{session_id}': {cart_summary}")
    return f"The cart contains: {cart_summary}."

@tool
def clear_cart(session_id: str) -> str:
    """
    Empties the shopping cart.
    """
    logger.info(f"Tool: clear_cart called for session '{session_id}'.")
    cart = get_cart_for_session(session_id)
    
    cart.clear()
    logger.info(f"Cart for session '{session_id}' has been cleared.")
    return "The cart has been cleared."

cart_tools = [add_to_cart, remove_from_cart, view_cart, clear_cart]