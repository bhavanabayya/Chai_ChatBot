import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from state.session import get_paypal_order_id, set_paypal_order_id
from tools.payment.paypal.paypal_tool import create_paypal_order, capture_paypal_order

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/paypal", tags=["paypal"])

class SaveOrder(BaseModel):
    order_id: str

@router.post("/paypal_order_id")
def save(o: SaveOrder):
    logger.info(f"Received request to save PayPal order ID: {o.order_id}")
    try:
        set_paypal_order_id(o.order_id)
        logger.info("Successfully saved PayPal order ID.")
        return {"ok": True}
    except Exception as e:
        logger.error(f"Failed to save PayPal order ID: {o.order_id}. Error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/paypal_order_id")
def get():
    logger.info("Received request to get PayPal order ID.")
    try:
        order_id = get_paypal_order_id()
        logger.info(f"Successfully retrieved PayPal order ID: {order_id}")
        return {"order_id": order_id}
    except Exception as e:
        logger.error(f"Failed to get PayPal order ID. Error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

class CreateOrder(BaseModel):
    amount: str
    currency: str = "USD"

@router.post("/order")
def order(req: CreateOrder):
    logger.info(f"Received request to create PayPal order for amount: {req.amount} {req.currency}")
    try:
        result = create_paypal_order(req.amount, req.currency)
        logger.info(f"Successfully created PayPal order. Order ID: {result.get('id')}")
        return result
    except Exception as e:
        logger.error(f"Failed to create PayPal order. Error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/capture/{order_id}")
def capture(order_id: str):
    logger.info(f"Received request to capture PayPal order with ID: {order_id}")
    try:
        result = capture_paypal_order(order_id)
        logger.info(f"Successfully captured PayPal order: {order_id}.")
        return result
    except Exception as e:
        logger.error(f"Failed to capture PayPal order with ID: {order_id}. Error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))