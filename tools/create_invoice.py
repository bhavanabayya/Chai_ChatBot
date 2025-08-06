from langchain.tools import tool
from tools.quickbooks_wrapper import QuickBooksWrapper
import re

@tool
def create_invoice_tool(input_text: str) -> str:
    """
    Generates a QuickBooks invoice from input text like '2 Masala Chai and 1 Ginger Chai'.
    Defaults to customer ID 58.
    """

    #  Use default customer if none provided
    customer_match = re.search(r"customer\s+(\d+)", input_text, re.IGNORECASE)
    customer_id = customer_match.group(1) if customer_match else "58"

    item_matches = re.findall(r"(\d+)\s+([a-zA-Z\s]+?)(?:,|and|for|$)", input_text, re.IGNORECASE)
    if not item_matches:
        return " Could not parse item quantities. Try using '2 Masala Chai and 1 Ginger Chai' format."

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
            return f" '{name}' is not on our menu. Please ask for the menu first."
        
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
    invoice = qb.create_invoice(customer_id, line_items)
    invoice_id = invoice["Invoice"]["Id"]
    doc_number = invoice["Invoice"].get("DocNumber", invoice_id)
    pdf_message = qb.get_invoice_pdf(invoice_id)
    pdf_url = f"http://localhost:8000/download/invoice/{invoice_id}"
    return f" Created Invoice #{doc_number} for Customer #{customer_id}.\n\n🧾 [Download Invoice PDF]({pdf_url})"

    