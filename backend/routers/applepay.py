import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from tools.payment.applepay.apple_pay_tool import (
    generate_apple_pay_link,
    get_apple_pay_session_status,
    save_apple_pay_session_id,
    get_apple_pay_session_id,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/applepay", tags=["applepay"])

class ApplePayLinkRequest(BaseModel):
    amount: float
    currency: str = "USD"
    order_id: Optional[str] = None
    description: Optional[str] = None

@router.post("/link")
def create_link(req: ApplePayLinkRequest):
    logger.info(f"Received request to create Apple Pay link for amount: {req.amount} {req.currency}")
    try:
        product_name = req.description or "Chai Corner Order"
        url = generate_apple_pay_link.invoke({"amount_dollars": req.amount, "product_name": product_name})
        logger.info(f"Successfully generated Apple Pay link: {url}")
        return {"url": url}
    except Exception as e:
        logger.error(f"Failed to create Apple Pay link. Error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/session/{session_id}")
def set_session(session_id: str):
    logger.info(f"Received request to set Apple Pay session ID: {session_id}")
    try:
        save_apple_pay_session_id(session_id)
        logger.info(f"Successfully saved Apple Pay session ID: {session_id}")
        return {"ok": True, "session_id": session_id}
    except Exception as e:
        logger.error(f"Failed to set Apple Pay session ID: {session_id}. Error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/session")
def get_session():
    logger.info("Received request to get Apple Pay session ID.")
    try:
        sid = get_apple_pay_session_id()
        logger.info(f"Successfully retrieved Apple Pay session ID: {sid}")
        return {"session_id": sid}
    except Exception as e:
        logger.error(f"Failed to get Apple Pay session ID. Error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status/{session_id}")
def status(session_id: str):
    logger.info(f"Received request to get Apple Pay session status for ID: {session_id}")
    try:
        result = get_apple_pay_session_status(session_id)
        logger.info(f"Successfully retrieved status for session ID {session_id}.")
        return result
    except Exception as e:
        logger.error(f"Failed to get Apple Pay session status for ID: {session_id}. Error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))