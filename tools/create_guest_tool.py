from langchain_core.tools import tool
from tools.quickbooks_wrapper import QuickBooksWrapper
import streamlit as st

@tool
def create_guest_tool(input: str) -> str:
    """
    Creates a guest customer profile in QuickBooks.
    Input format: "<some input> | customer_id: <id>"
    """

    guest_name = "Guest Customer"

    # Try extracting name
    if "| customer_id:" in input:
        user_input, _ = input.split("| customer_id:")
        if user_input.strip():
            guest_name = f"Guest {user_input.strip()}"

    qb = QuickBooksWrapper()

    try:
        created = qb.create_guest_customer(guest_name)

        # ✅ Store customer ID for downstream use
        st.session_state["customer_id"] = created["Id"]
        st.session_state["is_guest"] = True

        return f"✅ Created guest customer with ID: {created['Id']}"
    except Exception as e:
        return f"❌ Failed to create guest: {str(e)}"
