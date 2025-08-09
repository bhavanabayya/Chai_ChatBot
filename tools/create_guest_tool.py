from langchain_core.tools import tool
from tools.quickbooks_wrapper import QuickBooksWrapper
import json
from backend.chat_state import set_customer  # ✅ centralized

@tool
def create_guest_tool(input: str) -> str:
    """
    Creates a guest customer profile in QuickBooks.
    Skips if we already have a real customer.
    """
    from backend.chat_state import get_state
    state = get_state()

    # 🚫 Don't downgrade an existing real customer to guest
    if state.customer_id and not state.is_guest:
        return json.dumps({
            "status": "skipped",
            "reason": "already_real_customer",
            "id": state.customer_id
        })

    guest_name = "Guest Customer"
    if "| customer_id:" in input:
        user_input, _ = input.split("| customer_id:")
        if user_input.strip():
            guest_name = f"Guest {user_input.strip()}"

    qb = QuickBooksWrapper()
    try:
        created = qb.create_guest_customer(guest_name)
        set_customer(created["Id"], is_guest=True)
        return json.dumps({
            "status": "guest_created",
            "id": created["Id"],
            "name": created.get("DisplayName", guest_name)
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to create guest: {str(e)}"
        })
