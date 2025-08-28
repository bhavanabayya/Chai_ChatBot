import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from tools.quickbooks.create_invoice_tool import create_invoice_tool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quickbooks", tags=["quickbooks"])

class Item(BaseModel):
    name: str
    quantity: int

class InvoiceRequest(BaseModel):
    session_id: str
    items: List[Item]
    note: Optional[str] = None

@router.post("/invoice")
def create_invoice(req: InvoiceRequest):
    logger.info(f"Received request to create invoice for session_id: {req.session_id}")
    try:
        items_text = ", ".join([f"{i.quantity} {i.name}" for i in req.items])
        prompt = f"{items_text}"
        if req.note: 
            prompt += f" Note: {req.note}."
            
        logger.debug(f"Prompt for create_invoice_tool: {prompt}")
        
        result = create_invoice_tool(prompt, req.session_id)
        
        logger.info(f"Successfully created invoice. Result: {result}")
        
        return result
    except Exception as e:
        logger.error(f"Failed to create invoice for session_id: {req.session_id}. Error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
