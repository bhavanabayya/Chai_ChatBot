from langchain_core.tools import tool
from pydantic import BaseModel
from typing import Optional
from tools.quickbooks_wrapper import QuickBooksWrapper

class RenameInput(BaseModel):
    customer_id: str
    new_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None

@tool(args_schema=RenameInput)
def rename_customer_tool(customer_id: str, new_name: str, phone: Optional[str] = None,
                         email: Optional[str] = None, address_line1: Optional[str] = None,
                         city: Optional[str] = None, state: Optional[str] = None, postal_code: Optional[str] = None) -> str:
    """
    Renames a guest to a real customer and optionally adds contact details.
    """
    if not customer_id or customer_id == "None":
        return "❌ Cannot rename: customer ID is missing or invalid."

    qb = QuickBooksWrapper()

    address = None
    if address_line1 and city and state and postal_code:
        address = {
            "Line1": address_line1,
            "City": city,
            "CountrySubDivisionCode": state,
            "PostalCode": postal_code
        }

    try:
        updated = qb.rename_customer(customer_id, new_name, phone=phone, email=email, address=address)
        return f"✅ Renamed and updated customer {customer_id} to '{new_name}'"
    except Exception as e:
        return f"❌ Rename failed: {str(e)}"
