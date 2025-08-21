from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from tools.fedex.fedex_tool import create_fedex_shipment
router = APIRouter(prefix="/api/fedex", tags=["fedex"])
class LabelRequest(BaseModel):
    payload: Dict[str, Any]
@router.post("/label")
def label(req: LabelRequest):
    try:
        return create_fedex_shipment(req.payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
