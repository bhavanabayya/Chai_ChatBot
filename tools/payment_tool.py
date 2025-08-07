import os
from langchain.agents import Tool
from langchain_core.tools import tool
from dotenv import load_dotenv

from paypal_agent_toolkit.langchain.toolkit import PayPalToolkit
from paypal_agent_toolkit.shared.configuration import Configuration, Context

load_dotenv()

# Global variable for order ID (consider using a persistent store in production)
order_id = ""

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

    configuration = Configuration(
        actions={
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

    toolkit = PayPalToolkit(
        client_id=paypal_client_id,
        secret=paypal_client_secret,
        configuration=configuration
    )

    return toolkit.get_tools()

@tool
def save_order_id(new_order_id: str) -> str:
    """
    Saves the provided PayPal order ID to a global variable for later use.
    Args:
        new_order_id (str): The PayPal order ID to save.
    Returns:
        str: Confirmation message.
    """
    global order_id
    order_id = new_order_id
    return f"Order ID '{order_id}' has been saved successfully."

@tool
def get_order_id() -> str:
    """
    Retrieves the previously saved PayPal order ID.
    Returns:
        str: The saved PayPal order ID, or a message if none saved.
    """
    if order_id:
        return order_id
    else:
        return "No order ID has been saved yet."

# Combine PayPal tools with custom order tools
order_tools = get_paypal_tools() + [save_order_id, get_order_id]
