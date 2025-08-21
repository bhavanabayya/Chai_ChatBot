from langchain_core.tools import tool
from tools.quickbooks.quickbooks_wrapper import QuickBooksWrapper
import json
from state.session import set_customer

@tool
def create_guest_tool(session_id: str, name: str) -> str:
    """
    Creates a guest customer profile in QuickBooks.
    Skips if we already have a real customer.
    """
    from state.session import get_state
    state = get_state(session_id)

    # 🚫 Don't downgrade an existing real customer to guest
    if state.customer_id and not state.is_guest:
        return json.dumps({
            "status": "skipped",
            "reason": "already_real_customer",
            "id": state.customer_id
        })

    # The agent passes just the user's name directly to this tool
    # Add "Guest" prefix to the user's name
    if name.strip():
        guest_name = f"Guest {name.strip()}"
    else:
        guest_name = "Guest Customer"

    qb = QuickBooksWrapper()
    try:
        created = qb.create_guest_customer(guest_name)
        set_customer(session_id, created["Id"], is_guest=True)
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
