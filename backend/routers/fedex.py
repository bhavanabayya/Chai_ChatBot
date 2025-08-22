import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from tools.fedex.fedex_tool import create_fedex_shipment

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fedex", tags=["fedex"])

class LabelRequest(BaseModel):
    payload: Dict[str, Any]

@router.post("/label")
def label(req: LabelRequest):
    logger.info("Received request to create FedEx label.")
    try:
        logger.debug(f"Payload for shipment: {req.payload}")
        result = create_fedex_shipment(req.payload)
        logger.info("Successfully created FedEx shipment label.")
        return result
    except Exception as e:
        logger.error(f"Failed to create FedEx shipment label. Error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))