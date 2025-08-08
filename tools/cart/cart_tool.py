from collections import defaultdict
from langchain_core.tools import tool
import streamlit as st

# --- In-memory Global Cart Storage ---
# This dictionary will store items for a single, global shopping cart.
# In a real application, this might be tied to a session ID or user ID.
# Structure: {item_name: quantity, ...}
if "cart" not in st.session_state:
    st.session_state.cart = defaultdict(int)

@tool
def add_to_cart(item_name: str, quantity: int) -> str:
    """
    Adds a specified quantity of an item to the global shopping cart.
    Args:
        item_name (str): The name of the item to add (e.g., "Espresso Pods", "Decaf Pods").
        quantity (int): The quantity of the item to add. Must be a positive integer.
    Returns:
        str: A confirmation message about the item added to the cart.
    """
    if "cart" not in st.session_state:
        st.session_state.cart = defaultdict(int)
    if quantity <= 0:
        return "Quantity must be a positive integer to add to cart."
    st.session_state.cart[item_name] += quantity
    print(f"--- TOOL CALL: add_to_cart ---")
    print(f"Item: {item_name}, Quantity: {quantity}")
    return f"Added {quantity} x {item_name} to the cart. Current quantity: {st.session_state.cart[item_name]}."

@tool
def remove_from_cart(item_name: str, quantity: int) -> str:
    """
    Removes a specified quantity of an item from the global shopping cart.
    If the quantity to remove exceeds the quantity in the cart, the item is fully removed.
    Args:
        item_name (str): The name of the item to remove.
        quantity (int): The quantity of the item to remove. Must be a positive integer.
    Returns:
        str: A confirmation message about the item removed from the cart.
    """
    if "cart" not in st.session_state:
        st.session_state.cart = defaultdict(int)
    if quantity <= 0:
        return "Quantity must be a positive integer to remove from cart."
    if item_name not in st.session_state.cart or st.session_state.cart[item_name] == 0:
        return f"{item_name} is not in the cart."

    current_quantity = st.session_state.cart[item_name]
    if quantity >= current_quantity:
        del st.session_state.cart[item_name]
        print(f"--- TOOL CALL: remove_from_cart ---")
        print(f"Item: {item_name}, Quantity: all removed")
        return f"Removed all {current_quantity} x {item_name} from the cart."
    else:
        st.session_state.cart[item_name] -= quantity
        print(f"--- TOOL CALL: remove_from_cart ---")
        print(f"Item: {item_name}, Quantity: {quantity}")
        return f"Removed {quantity} x {item_name} from the cart. Remaining quantity: {st.session_state.cart[item_name]}."

@tool
def view_cart() -> str:
    """
    Displays the current contents of the global shopping cart.
    Returns:
        str: A string listing the items and quantities in the cart, or a message if the cart is empty.
    """
    
    if "cart" not in st.session_state:
        st.session_state.cart = defaultdict(int)
    elif not st.session_state.cart:
        print(f"--- TOOL CALL: view_cart ---")
        print(f"Cart: Empty")
        return f"The cart is currently empty."
    
    cart_items = [f"{qty} x {item}" for item, qty in st.session_state.cart.items()]
    cart_summary = ", ".join(cart_items)
    print(f"--- TOOL CALL: view_cart ---")
    print(f"Cart: {cart_summary}")
    return f"The cart contains: {cart_summary}."

@tool
def clear_cart() -> str:
    """
    Empties the global shopping cart.
    Returns:
        str: A confirmation message that the cart has been cleared.
    """
    
    if "cart" not in st.session_state:
        st.session_state.cart = defaultdict(int)
    st.session_state.cart.clear()
    print(f"--- TOOL CALL: clear_cart ---")
    print(f"Cart: Cleared")
    return f"The cart has been cleared."

cart_tools = [add_to_cart, remove_from_cart, view_cart, clear_cart]