from langchain.tools import tool
from tools.quickbooks_wrapper import QuickBooksWrapper
import re
import streamlit as st

@tool
def create_invoice_tool(input_text: str) -> str:
    """
    Creates a QuickBooks invoice from order text and embedded customer ID.
    Accepts formats like:
    - "6 Masala Chai | customer_id: 6"
    - "6 Masala Chai for customer 6"
    """

    # 1️⃣ Try to get from session state
    customer_id = st.session_state.get("customer_id", None)

    # 2️⃣ Fallback: extract "for customer 6"
    if not customer_id:
        match = re.search(r"customer\s+(\d+)", input_text, re.IGNORECASE)
        if match:
            customer_id = match.group(1)

    # 3️⃣ Fallback: extract "| customer_id: 6"
    if not customer_id and "| customer_id:" in input_text:
        try:
            _, extracted = input_text.split("| customer_id:")
            customer_id = extracted.strip()
        except Exception:
            return "❌ Could not extract customer ID from input."

    if not customer_id:
        return "⚠️ Cannot create invoice: Customer ID is missing. Please validate the customer first."

    # ✅ Extract items
    item_matches = re.findall(r"(\d+)\s+([a-zA-Z\s]+?)(?:,|and|for|$)", input_text, re.IGNORECASE)
    if not item_matches:
        return "⚠️ Could not parse item quantities. Use format like '2 Masala Chai and 1 Ginger Chai'."

    name_to_id = {
        "masala chai": ("21", 20),
        "ginger chai": ("22", 15),
        "madras coffee": ("19", 20),
        "elaichi chai": ("20", 16)
    }

    line_items = []
    for i, (qty, name) in enumerate(item_matches, start=1):
        name = name.strip().lower()
        item_info = name_to_id.get(name)
        if not item_info:
            return f"⚠️ '{name}' is not on our menu."
        item_id, price = item_info
        line_items.append({
            "Description": name.title(),
            "DetailType": "SalesItemLineDetail",
            "SalesItemLineDetail": {
                "Qty": int(qty),
                "UnitPrice": price,
                "ItemRef": {
                    "name": name.title(),
                    "value": item_id
                }
            },
            "LineNum": i,
            "Amount": int(qty) * price,
            "Id": str(i)
        })

    qb = QuickBooksWrapper()
    try:
        invoice = qb.create_invoice(customer_id, line_items)
        invoice_id = invoice["Invoice"]["Id"]
        doc_number = invoice["Invoice"].get("DocNumber", invoice_id)
        pdf_url = f"http://localhost:8000/download/invoice/{invoice_id}"
        return f"✅ Created Invoice #{doc_number} for Customer #{customer_id}.\n🧾 [Download PDF]({pdf_url})"
    except Exception as e:
        return f"❌ Failed to create invoice: {str(e)}"
