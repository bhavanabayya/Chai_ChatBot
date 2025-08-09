# tools/create_customer_tool.py
from langchain_core.tools import tool
from tools.quickbooks_wrapper import QuickBooksWrapper
import streamlit as st
import json

@tool
def create_customer_tool(input: str) -> str:
    """
    Creates a full (non-guest) customer in QuickBooks.
    Expects JSON in input:
      {
        "display_name": "John Doe",
        "phone": "555-1234",
        "email": "john@example.com",
        "address": {
            "Line1": "123 Main St",
            "City": "Los Angeles",
            "CountrySubDivisionCode": "CA",
            "PostalCode": "90001"
        }
      }
    """
    try:
        data = json.loads(input) if input.strip().startswith("{") else {}
    except Exception:
        return json.dumps({"status": "error", "message": "Invalid JSON for create_customer_tool"})

    display_name = data.get("display_name")
    phone = data.get("phone")
    email = data.get("email")
    address = data.get("address")

    if not display_name:
        return json.dumps({"status": "error", "message": "display_name is required"})

    qb = QuickBooksWrapper()
    try:
        customer = qb.create_customer(display_name, phone, email, address)
        # ✅ Critical: promote to real customer
        st.session_state["customer_id"] = customer["Id"]
        st.session_state["is_guest"] = False

        return json.dumps({
            "status": "created",
            "id": customer["Id"],
            "name": customer.get("DisplayName", display_name)
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
