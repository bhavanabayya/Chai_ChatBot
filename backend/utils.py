# backend/utils.py (or put directly in main.py)
import json, re
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

_ID_KEYS = {"customer_id", "customerId", "id", "CustomerRef", "CustomerRef.value"}

def extract_id_from_response(raw: Any) -> Optional[str]:
    """
    Try hard to pull a customer id out of an LLM/tool response.
    Accepts dicts, JSON strings, or free text. Returns None if not found.
    """
    logger.debug(f"Attempting to extract ID from raw input type: {type(raw)}")
    
    # 1) Dict-like
    if isinstance(raw, dict):
        # direct keys
        for k in ("customer_id", "customerId", "id"):
            v = raw.get(k)
            if isinstance(v, (str, int)) and str(v).strip():
                logger.debug(f"Found ID in dict from key '{k}': {v}")
                return str(v).strip()
        # nested QuickBooks-ish
        cref = raw.get("CustomerRef")
        if isinstance(cref, dict) and cref.get("value"):
            logger.debug(f"Found nested QuickBooks-style ID: {cref['value']}")
            return str(cref["value"]).strip()
        logger.debug("No ID found in dict.")

    # 2) String → try JSON first
    if isinstance(raw, (str, bytes)):
        text = raw.decode() if isinstance(raw, bytes) else raw
        text = text.strip()
        logger.debug(f"Input is a string. Attempting to parse.")

        # JSON object?
        if text.startswith("{") and text.endswith("}"):
            try:
                obj = json.loads(text)
                logger.debug("String is valid JSON. Recursing.")
                return extract_id_from_response(obj)
            except Exception as e:
                logger.warning(f"String appears to be JSON but failed to parse: {e}")
                pass

        # Look for "customer_id": "12345" or 'customer_id': 12345, etc.
        m = re.search(r'(customer[_ ]?id|customerId|CustomerRef\.value)\s*["\':]*\s*([{\[])?\s*"?([A-Za-z0-9\-]+)"?', text)
        if m:
            logger.debug(f"Found ID via regex pattern: {m.group(3)}")
            return m.group(3)

        # Fallback: any long-ish numeric token
        m2 = re.search(r'\b\d{6,}\b', text)
        if m2:
            logger.debug(f"Found ID via fallback numeric pattern: {m2.group(0)}")
            return m2.group(0)
    
    logger.debug("No ID could be extracted from the input.")
    return None