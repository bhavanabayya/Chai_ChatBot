from langchain_core.tools import tool
from tools.fedex.fedex_api_wrapper import FedExWrapper

@tool
def create_fedex_shipment() -> str:
    """
    Creates a FedEx shipment using sandbox credentials.
    Returns tracking number and label URL.
    """
    fedex = FedExWrapper()
    result = fedex.create_shipment()

    if not result["success"]:
        return f" Failed to create FedEx shipment.\nError: {result['error']}"

    label_url = result["label_url"] or "Label not available"
    return (
        f" Shipment Created!\n"
        f"Label URL: {label_url}"
    )
