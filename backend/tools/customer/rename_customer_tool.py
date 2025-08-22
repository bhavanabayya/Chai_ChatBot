import logging
from langchain_core.tools import tool
from pydantic import BaseModel
from typing import Optional
from tools.quickbooks.quickbooks_wrapper import QuickBooksWrapper
import json
from state.session import set_customer

logger = logging.getLogger(__name__)

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
    logger.info(f"Tool 'rename_customer_tool' called for session_id: {session_id} to rename customer ID: {customer_id} to '{new_name}'")

    if not customer_id or customer_id == "None":
        logger.error("Cannot rename: customer ID is missing or invalid.")
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
        logger.debug(f"Address details provided: {address}")

    try:
        updated = qb.rename_customer(customer_id, new_name, phone, email, address)
        set_customer(session_id, updated["Id"], is_guest=False)
        logger.info(f"Customer successfully renamed to '{new_name}'. App state updated.")
        return json.dumps({"status": "renamed", "id": updated["Id"], "name": updated["DisplayName"]})
    except Exception as e:
        logger.error(f"Rename failed for customer ID {customer_id}. Error: {str(e)}", exc_info=True)
        return json.dumps({"status": "error", "message": f"Rename failed: {str(e)}"})