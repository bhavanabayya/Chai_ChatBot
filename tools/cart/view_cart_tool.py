# tools/view_cart_tool.py

from langchain_core.tools import tool
from tools.add_to_cart_tool import cart  # if you're storing cart in that module

@tool
def view_cart(_: str = "") -> str:
    """
    Returns the current contents of the cart.
    """
    if not cart:
        return " Your cart is empty."

    return " Your cart:\n" + "\n".join(f"- {item}" for item in cart)

view_cart_tool = view_cart
