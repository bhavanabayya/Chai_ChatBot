import logging
from langchain_core.tools import tool
from tools.fedex.fedex_api_wrapper import FedExWrapper

logger = logging.getLogger(__name__)

@tool
def create_fedex_shipment() -> str:
    """
    Creates a FedEx shipment using sandbox credentials.
    Returns tracking number and label URL.
    """
    logger.info("Invoking create_fedex_shipment tool.")
    
    try:
        fedex = FedExWrapper()
        result = fedex.create_shipment()
        
        if not result["success"]:
            logger.error(f"FedEx shipment failed. Error: {result['error']}")
            return f" Failed to create FedEx shipment.\nError: {result['error']}"

        label_url = result["label_url"] or "Label not available"
        logger.info(f"FedEx shipment created successfully. Label URL: {label_url}")
        
        return (
            f" Shipment Created!\n"
            f"Label URL: {label_url}"
        )
    except Exception as e:
        logger.error(f"An exception occurred while using FedExWrapper: {e}", exc_info=True)
        return f"An error occurred while creating a FedEx shipment: {e}"