from langchain.agents import tool
from Authentication import get_fedex_token
from Create_Shipment import create_shipment

@tool
def create_fedex_shipment() -> str:
    """
    Creates a FedEx shipment using sandbox credentials.
    Returns tracking number and label URL.
    """
    token = get_fedex_token()
    result = create_shipment(token)

    if "error" in result:
        return f"❌ FedEx Shipment Failed: {result['error']}\nDetails: {result.get('details', '')}"

    shipment = result['output']['transactionShipments'][0]
    tracking = shipment['masterTrackingNumber']
    label_url = shipment['pieceResponses'][0]['packageDocuments'][0]['url']
    
    # local_file_path = download_label(label_url)

    msg = (
        f"📦 Shipment Created!\n"
        f"Tracking: {tracking}\n"
        f"Label URL: {label_url}"
    )

    print(f"DEBUG: returning string:\n{msg}")
    return msg

