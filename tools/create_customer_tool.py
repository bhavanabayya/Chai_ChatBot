# tools/create_customer_tool.py

from langchain_core.tools import tool
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
import streamlit as st
import json

from tools.quickbooks_wrapper import QuickBooksWrapper


class CreateCustomerInput(BaseModel):
    """Inputs for creating a full QuickBooks customer."""
    first_name: str = Field(..., description="Customer first name")
    last_name: str = Field(..., description="Customer last name")
    phone: Optional[str] = Field(None, description="Phone number, e.g. 555-123-4567")
    email: Optional[EmailStr] = Field(None, description="Email address")
    address_line1: Optional[str] = Field(None, description="Street address line 1")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State/Province code, e.g. CA")
    postal_code: Optional[str] = Field(None, description="Postal/ZIP code")


@tool(args_schema=CreateCustomerInput)
def create_customer_tool(
    first_name: str,
    last_name: str,
    phone: Optional[str] = None,
    email: Optional[EmailStr] = None,
    address_line1: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    postal_code: Optional[str] = None,
) -> str:
    """
    Creates a full (non-guest) customer in QuickBooks (or returns the existing one).
    On success, sets Streamlit session_state:
      - customer_id -> the customer's QuickBooks Id
      - is_guest -> False
    Returns a JSON string: {"status":"created|exists","id":"...","name":"..."}.
    """
    display_name = f"{first_name.strip()} {last_name.strip()}"

    # Build address dict only if any address detail is provided
    address = None
    if any([address_line1, city, state, postal_code]):
        address = {
            "Line1": address_line1 or "",
            "City": city or "",
            "CountrySubDivisionCode": state or "",
            "PostalCode": postal_code or "",
        }

    qb = QuickBooksWrapper()

    # Check if already exists to label status correctly
    existing = qb.find_customer_by_name(display_name)
    if existing:
        st.session_state["customer_id"] = existing["Id"]
        st.session_state["is_guest"] = False
        return json.dumps({"status": "exists", "id": existing["Id"], "name": display_name})

    # Create new customer with optional fields
    created = qb.create_customer(
        display_name=display_name,
        phone=phone,
        email=str(email) if email else None,
        address=address,
    )

    st.session_state["customer_id"] = created["Id"]
    st.session_state["is_guest"] = False
    return json.dumps({"status": "created", "id": created["Id"], "name": display_name})
