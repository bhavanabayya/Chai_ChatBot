from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from tools.customer.validate_customer_tool import validate_customer_tool
from tools.customer.create_customer_tool import create_customer_tool
from tools.customer.create_guest_tool import create_guest_tool
from tools.customer.rename_customer_tool import rename_customer_tool
router = APIRouter(prefix="/api/customer", tags=["customer"])
class ValidateRequest(BaseModel):
    session_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
@router.post("/validate")
def validate(req: ValidateRequest):
    try:
        return validate_customer_tool(req.session_id, req.name, req.email, req.phone)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
class CreateCustomerRequest(BaseModel):
    session_id: str
    name: str
    email: str
    phone: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
@router.post("/create")
def create(req: CreateCustomerRequest):
    try:
        return create_customer_tool(req.session_id, req.name, req.email, req.phone, req.metadata or {})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
class CreateGuestRequest(BaseModel):
    session_id: str
    nickname: str
@router.post("/guest")
def guest(req: CreateGuestRequest):
    try:
        return create_guest_tool(req.session_id, req.nickname)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
class RenameRequest(BaseModel):
    session_id: str
    old_name: str
    new_name: str
@router.post("/rename")
def rename(req: RenameRequest):
    try:
        return rename_customer_tool(req.session_id, req.old_name, req.new_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
