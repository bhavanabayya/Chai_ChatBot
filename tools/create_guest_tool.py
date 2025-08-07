from langchain_core.tools import tool
from tools.quickbooks_wrapper import QuickBooksWrapper

@tool
def create_guest_tool(input: str) -> str:
    """
    Creates a guest customer profile in QuickBooks.
    Input format: "<some input> | customer_id: <id>"
    """
    # Default guest name
    guest_name = "Guest Customer"

    # Try extracting a name from input (before the customer_id part)
    if "| customer_id:" in input:
        user_input, _ = input.split("| customer_id:")
        if user_input.strip():
            guest_name = f"Guest {user_input.strip()}"

    qb = QuickBooksWrapper()

    try:
        created = qb.create_guest_customer(guest_name)
        return f"✅ Created guest customer with ID: {created['Id']}"
    except Exception as e:
        return f"❌ Failed to create guest: {str(e)}"
