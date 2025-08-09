from langchain_core.tools import tool
from tools.quickbooks_wrapper import QuickBooksWrapper
import streamlit as st
import json

@tool
def validate_customer_tool(input: str) -> str:
    """
    Checks if customer exists by name. Does NOT create a guest. 
    Sets session_state.customer_id / is_guest for the UI.
    Returns a JSON string: {"status": "found"|"not_found", "name": str, "id": str|None}
    """
    name = input.split("| customer_id:")[0].strip() if "| customer_id:" in input else input.strip()

    qb = QuickBooksWrapper()
    customer = qb.find_customer_by_name(name)

    if customer:
        st.session_state["customer_id"] = customer["Id"]
        st.session_state["is_guest"] = False
        return json.dumps({"status": "found", "name": customer["DisplayName"], "id": customer["Id"]})
    else:
        # do NOT create guest here
        return json.dumps({"status": "not_found", "name": name, "id": None})
