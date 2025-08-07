# tools/rename_customer_tool.py
from langchain.tools import tool
from tools.quickbooks_wrapper import QuickBooksWrapper

@tool
def rename_customer_tool(customer_id: str, new_name: str) -> str:
    """
    Renames a customer to a new name if that name isn't already taken.
    """
    qb = QuickBooksWrapper()

    existing = qb.find_customer_by_name(new_name)
    if existing:
        return f"⚠️ Cannot rename: A customer with the name '{new_name}' already exists (ID: {existing['Id']})."

    try:
        updated = qb.rename_customer(customer_id, new_name)
        return f"✅ Renamed customer {customer_id} to '{new_name}'"
    except Exception as e:
        return f"❌ Rename failed: {str(e)}"

