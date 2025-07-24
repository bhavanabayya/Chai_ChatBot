from langchain_core.tools import tool

@tool
def generate_shipping_label(order_id: str) -> str:
    """
    Generate a FedEx shipping label for the given order ID.
    """
    label_link = f"https://fedex.example.com/label/{order_id}"
    return f"🚚 Shipping label generated! Track your shipment here: {label_link}"

fedex_tool = generate_shipping_label