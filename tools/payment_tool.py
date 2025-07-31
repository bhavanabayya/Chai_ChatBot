import os
from langchain.agents import Tool
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

# Combine with other payment methods
# payment_tool = generate_payment_link
