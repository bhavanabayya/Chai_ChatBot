from langchain_core.tools import tool
from pydantic import BaseModel
from typing import Optional
from tools.quickbooks.quickbooks_wrapper import QuickBooksWrapper
import json
from state.session import set_customer  # ✅ centralized

class RenameInput(BaseModel):
    session_id: str
    customer_id: str
    new_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None

@tool(args_schema=RenameInput)
def rename_customer_tool(
    session_id: str,
    customer_id: str,
    new_name: str,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    address_line1: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    postal_code: Optional[str] = None,
) -> str:
    """
    Renames a guest to a real customer and optionally updates contact details.
    Returns JSON: {"status":"renamed","id":"...","name":"..."} on success.
    """
    if not customer_id or customer_id == "None":
        return json.dumps({"status": "error", "message": "Cannot rename: customer ID is missing or invalid."})

    qb = QuickBooksWrapper()

    address = None
    if any([address_line1, city, state, postal_code]):
        address = {
            "Line1": address_line1 or "",
            "City": city or "",
            "CountrySubDivisionCode": state or "",
            "PostalCode": postal_code or "",
        }

    try:
        updated = qb.rename_customer(customer_id, new_name, phone, email, address)
        set_customer(session_id, updated["Id"], is_guest=False)  # ✅ promote centrally
        return json.dumps({"status": "renamed", "id": updated["Id"], "name": updated["DisplayName"]})
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Rename failed: {str(e)}"})
