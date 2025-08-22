import logging
from langchain_core.tools import tool
from tools.quickbooks.quickbooks_wrapper import QuickBooksWrapper
import json
from state.session import set_customer

logger = logging.getLogger(__name__)

@tool
def validate_customer_tool(session_id:str, input: str) -> str:
    """
    Checks if customer exists by name. Does NOT create a guest.
    Returns JSON: {"status":"found"|"not_found","name": str,"id": str|None}
    """
    logger.info(f"Tool 'validate_customer_tool' called for session '{session_id}' with input: '{input}'")
    name = input.split("| customer_id:")[0].strip() if "| customer_id:" in input else input.strip()
    
    qb = QuickBooksWrapper()
    customer = qb.find_customer_by_name(name)

    if customer:
        set_customer(session_id, customer["Id"], is_guest=False)
        logger.info(f"Customer '{name}' found with ID '{customer['Id']}'. App state updated.")
        return json.dumps({"status": "found", "name": customer["DisplayName"], "id": customer["Id"]})
    else:
        logger.info(f"Customer '{name}' not found. App state remains unchanged.")
        # leave state unchanged; the agent decides next step
        return json.dumps({"status": "not_found", "name": name, "id": None})