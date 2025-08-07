import os
from langchain.agents import Tool
from langchain_core.tools import tool
from dotenv import load_dotenv

from paypal_agent_toolkit.langchain.toolkit import PayPalToolkit
from paypal_agent_toolkit.shared.configuration import Configuration, Context

load_dotenv()

def get_paypal_tools() -> list[Tool]:
    """
    Initializes the PayPal Toolkit and returns a list of LangChain tools.

    Returns:
        list[Tool]: A list of tools for creating, getting, and capturing PayPal orders.
    
    Raises:
        ValueError: If PayPal credentials are not found in the environment variables.
    """

    paypal_client_id = os.getenv("PAYPAL_CLIENT_ID")
    paypal_client_secret = os.getenv("PAYPAL_CLIENT_SECRET")

    if not paypal_client_id or not paypal_client_secret:
        raise ValueError(
            "PayPal client ID and secret must be set in environment variables."
        )

    # Configure the allowed actions for the PayPal agent
    configuration = Configuration(
        actions={
            # "invoices": {
            #     "create": True,
            #     "list": True,
            #     "send": True,
            # },
            "orders": {
                "create": True,
                "get": True,
                "capture": True,
            }
        },
        context=Context(
            sandbox=True  # Use sandbox for development and testing
        )
    )

    # Initialize the toolkit
    toolkit = PayPalToolkit(
        client_id=paypal_client_id,
        secret=paypal_client_secret,
        configuration=configuration
    )

    return toolkit.get_tools()

# Combine with other payment methods later

#
#
#

order_id: str = ""

@tool
def save_order_id(new_order_id: str) -> str:
    """
    Saves the provided PayPal order ID to a global variable for later use.
    This is useful for persisting the order ID between different agent steps or calls.
    
    Args:
        new_order_id (str): The PayPal order ID to save.
        
    Returns:
        str: A confirmation message indicating the order ID has been saved.
    """
    global order_id
    order_id = new_order_id
    return f"Order ID '{order_id}' has been saved successfully."


@tool
def get_order_id() -> str:
    """
    Retrieves the previously saved PayPal order ID from a global variable.
    Use this tool to get the order ID that was saved using the `save_order_id` tool.
    
    Returns:
        str: The saved PayPal order ID, or a message if no ID has been saved yet.
    """
    if order_id:
        return order_id
    else:
        return "No order ID has been saved yet."


# payment_tool = get_paypal_tools()
order_tools = [save_order_id, get_order_id]
