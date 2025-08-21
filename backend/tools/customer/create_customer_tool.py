# tools/create_customer_tool.py
from langchain_core.tools import tool
from tools.quickbooks.quickbooks_wrapper import QuickBooksWrapper
from state.session import set_customer
import json

@tool
def create_customer_tool(session_id: str, input: str) -> str:
    """
    Creates (or fetches) a full, non-guest customer in QuickBooks and updates app state.

    Expected input (JSON string):
    {
      "display_name": "John Doe",                 # required
      "phone": "555-1234",                        # optional
      "email": "john@example.com",                # optional
      "address": {                                # optional
        "Line1": "123 Main St",
        "City": "Los Angeles",
        "CountrySubDivisionCode": "CA",
        "PostalCode": "90001"
      }
    }

    Returns (JSON string):
      {"status":"created"|"exists","id":"<QB Id>","name":"<DisplayName>"}
      or {"status":"error","message":"..."}
    """
    # --- Parse input ---
    try:
        data = json.loads(input) if input and input.strip().startswith("{") else {}
    except Exception:
        return json.dumps({"status": "error", "message": "Invalid JSON for create_customer_tool"})

    display_name = (data.get("display_name") or "").strip()
    phone = data.get("phone")
    email = data.get("email")
    address = data.get("address")

    if not display_name:
        return json.dumps({"status": "error", "message": "display_name is required"})

    # --- Create or fetch customer ---
    qb = QuickBooksWrapper()
    try:
        customer = qb.create_customer(display_name, phone, email, address)
        qb_id = customer["Id"]
        qb_name = customer.get("DisplayName", display_name)

        # ✅ Update centralized state (also ensures is_guest=False)
        set_customer(session_id, qb_id, is_guest=False)

        # Always return "created" status since this tool is only called when creating new customers
        # The QuickBooks wrapper handles deduplication internally, but from the agent's perspective,
        # this tool should only be called for new customer creation
        return json.dumps({
            "status": "created",
            "id": qb_id,
            "name": qb_name
        })

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
