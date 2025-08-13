from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from tools.paypal.payment_tool import get_order_id, save_order_id, create_paypal_order, capture_paypal_order

# from tools.paypal.payment_tool import get_order_id, save_order_id, create_paypal_order, capture_paypal_order
router = APIRouter(prefix="/api/paypal", tags=["paypal"])
class SaveOrder(BaseModel):
    order_id: str
@router.post("/save_order_id")
def save(o: SaveOrder):
    try:
        return {"ok": save_order_id(o.order_id)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@router.get("/order_id")
def get():
    try:
        return {"order_id": get_order_id()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
class CreateOrder(BaseModel):
    amount: str
    currency: str = "USD"
@router.post("/order")
def order(req: CreateOrder):
    try:
        return create_paypal_order(req.amount, req.currency)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@router.post("/capture/{order_id}")
def capture(order_id: str):
    try:
        return capture_paypal_order(order_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
