import logging
from langchain_core.tools import tool
from tools.quickbooks.quickbooks_wrapper import QuickBooksWrapper
import json
from state.session import set_customer, get_state

logger = logging.getLogger(__name__)

@tool
def create_guest_tool(session_id: str, name: str) -> str:
    """
    Creates a guest customer profile in QuickBooks.
    Skips if we already have a real customer.
    """
    logger.info(f"Tool 'create_guest_tool' called for session_id: {session_id} with name: '{name}'")
    state = get_state(session_id)

    # 🚫 Don't downgrade an existing real customer to guest
    if state.customer_id and not state.is_guest:
        logger.info(f"Skipping guest creation for session '{session_id}' as a real customer already exists.")
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
        logger.info(f"Guest customer '{guest_name}' with ID '{created['Id']}' created and app state updated.")
        return json.dumps({
            "status": "guest_created",
            "id": created["Id"],
            "name": created.get("DisplayName", guest_name)
        })
    except Exception as e:
        logger.error(f"Failed to create guest for session '{session_id}'. Error: {str(e)}", exc_info=True)
        return json.dumps({
            "status": "error",
            "message": f"Failed to create guest: {str(e)}"
        })