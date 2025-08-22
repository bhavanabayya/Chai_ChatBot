import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from tools.customer.validate_customer_tool import validate_customer_tool
from tools.customer.create_customer_tool import create_customer_tool
from tools.customer.create_guest_tool import create_guest_tool
from tools.customer.rename_customer_tool import rename_customer_tool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/customer", tags=["customer"])

class ValidateRequest(BaseModel):
    session_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None

@router.post("/validate")
def validate(req: ValidateRequest):
    logger.info(f"Received request to validate customer for session_id: {req.session_id}")
    try:
        result = validate_customer_tool(req.session_id, req.name, req.email, req.phone)
        logger.info(f"Customer validation successful for session_id: {req.session_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to validate customer for session_id: {req.session_id}. Error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

class CreateCustomerRequest(BaseModel):
    session_id: str
    name: str
    email: str
    phone: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@router.post("/create")
def create(req: CreateCustomerRequest):
    logger.info(f"Received request to create customer '{req.name}' for session_id: {req.session_id}")
    try:
        result = create_customer_tool(req.session_id, req.name, req.email, req.phone, req.metadata or {})
        logger.info(f"Customer '{req.name}' created successfully.")
        return result
    except Exception as e:
        logger.error(f"Failed to create customer '{req.name}'. Error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

class CreateGuestRequest(BaseModel):
    session_id: str
    nickname: str

@router.post("/guest")
def guest(req: CreateGuestRequest):
    logger.info(f"Received request to create guest '{req.nickname}' for session_id: {req.session_id}")
    try:
        result = create_guest_tool(req.session_id, req.nickname)
        logger.info(f"Guest '{req.nickname}' created successfully.")
        return result
    except Exception as e:
        logger.error(f"Failed to create guest '{req.nickname}'. Error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

class RenameRequest(BaseModel):
    session_id: str
    old_name: str
    new_name: str

@router.post("/rename")
def rename(req: RenameRequest):
    logger.info(f"Received request to rename customer from '{req.old_name}' to '{req.new_name}' for session_id: {req.session_id}")
    try:
        result = rename_customer_tool(req.session_id, req.old_name, req.new_name)
        logger.info(f"Customer renamed successfully to '{req.new_name}'.")
        return result
    except Exception as e:
        logger.error(f"Failed to rename customer from '{req.old_name}'. Error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))