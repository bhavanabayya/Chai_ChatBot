
from langchain.tools import tool
from tools.quickbooks.quickbooks_wrapper import QuickBooksWrapper
import re
@tool("create_invoice_tool")
def create_invoice_tool(input_text: str) -> str:

    """
    Example: 'Generate 2 Madras Coffee and 1 Elaichi Chai for customer 58'
    """
    customer_match = re.search(r"customer\s+(\d+)", input_text, re.IGNORECASE)
    if not customer_match:
        return " Could not find customer ID."
    customer_id = customer_match.group(1)

    item_matches = re.findall(r"(\d+)\s+([a-zA-Z\s]+?)(?:,|and|for|$)", input_text, re.IGNORECASE)
    if not item_matches:
        return " Could not parse item quantities."

    name_to_id = {
        "elaichi chai": ("20", 16),
        "ginger chai": ("22", 15),
        "madras coffee": ("19", 20),
        "masala chai": ("21", 20),
    }

    line_items = []
    for i, (qty, name) in enumerate(item_matches, start=1):
        name = name.strip().lower()
        item_id, price = name_to_id.get(name, ("0", 0))
        if item_id == "0":
            continue
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

    pdf_link = f"http://localhost:8001/download/invoice/{invoice_id}"
    return f" Created Invoice #{doc_number}\n📄 [Download PDF Invoice]({pdf_link})"

    

invoice_tool = create_invoice_tool