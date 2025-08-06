from langchain_core.tools import tool

cart = []

@tool
def add_to_cart(item_string: str) -> str:
    """
    Adds a product to the user's cart. Example: '2 masala chai'
    """
    cart.append(item_string)
    return f" Added to cart: {item_string}"

add_to_cart_tool = add_to_cart
