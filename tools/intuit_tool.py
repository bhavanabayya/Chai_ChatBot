from langchain_core.tools import tool

@tool
def generate_invoice(order: str) -> str:
    """
    Generate an invoice for the given order.
    """
    invoice_url = f"https://example.com/invoice/{order.replace(' ', '_')}"
    return f"🧾 Invoice for order: {order} has been created. View it at: {invoice_url}"

intuit_tool = generate_invoice
