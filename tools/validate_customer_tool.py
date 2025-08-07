from langchain_core.tools import tool
from tools.quickbooks_wrapper import QuickBooksWrapper
import streamlit as st

@tool
def validate_customer_tool(input: str) -> str:
    """
    Checks if customer exists by name. Does NOT create a guest. Sets customer_id if found.
    """
    if "| customer_id:" in input:
        user_input, _ = input.split("| customer_id:")
    else:
        user_input = input.strip()

    qb = QuickBooksWrapper()
    customer = qb.find_customer_by_name(user_input.strip())

    if customer:
        st.session_state["customer_id"] = customer["Id"]
        st.session_state["is_guest"] = False
        return f"Customer exists: {customer['DisplayName']} (ID: {customer['Id']})"
    else:
        return "No customer found. You can create a guest profile if you'd like to proceed."
