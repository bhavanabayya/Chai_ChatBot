# tools/create_customer_tool.py
from langchain_core.tools import tool
from tools.quickbooks_wrapper import QuickBooksWrapper
from backend.chat_state import set_customer  # ✅ central source of truth
import json

@tool
def create_customer_tool(input: str) -> str:
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

        # Heuristic: QuickBooksWrapper.create_customer returns existing if name already exists.
        # We can mark this as "exists" when the returned DisplayName matches request.
        status = "exists" if qb_name.lower() == display_name.lower() else "created"

        # ✅ Update centralized state (also ensures is_guest=False)
        set_customer(qb_id, is_guest=False)

        return json.dumps({
            "status": status,
            "id": qb_id,
            "name": qb_name
        })

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
