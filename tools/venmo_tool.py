from langchain_core.tools import tool

@tool
def generate_venmo_payment_link(amount: str) -> str:
    """
    Generate a Venmo payment link for the customer to complete the payment.
    """
    return f"Please complete your payment of {amount} via Venmo: https://venmo.com/u/kuttybayya"

venmo_tool = generate_venmo_payment_link
