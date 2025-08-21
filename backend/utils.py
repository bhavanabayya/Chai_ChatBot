# backend/utils.py (or put directly in main.py)
import json, re
from typing import Optional, Any

_ID_KEYS = {"customer_id", "customerId", "id", "CustomerRef", "CustomerRef.value"}

def extract_id_from_response(raw: Any) -> Optional[str]:
    """
    Try hard to pull a customer id out of an LLM/tool response.
    Accepts dicts, JSON strings, or free text. Returns None if not found.
    """
    # 1) Dict-like
    if isinstance(raw, dict):
        # direct keys
        for k in ("customer_id", "customerId", "id"):
            v = raw.get(k)
            if isinstance(v, (str, int)) and str(v).strip():
                return str(v).strip()
        # nested QuickBooks-ish
        cref = raw.get("CustomerRef")
        if isinstance(cref, dict) and cref.get("value"):
            return str(cref["value"]).strip()

    # 2) String → try JSON first
    if isinstance(raw, (str, bytes)):
        text = raw.decode() if isinstance(raw, bytes) else raw
        text = text.strip()

        # JSON object?
        if text.startswith("{") and text.endswith("}"):
            try:
                obj = json.loads(text)
                return extract_id_from_response(obj)
            except Exception:
                pass

        # Look for "customer_id": "12345" or 'customer_id': 12345, etc.
        m = re.search(r'(customer[_ ]?id|customerId|CustomerRef\.value)\s*["\':]*\s*([{\[])?\s*"?([A-Za-z0-9\-]+)"?', text)
        if m:
            return m.group(3)

        # Fallback: any long-ish numeric token (e.g., QB realm-like or customer id)
        m2 = re.search(r'\b\d{6,}\b', text)
        if m2:
            return m2.group(0)

    return None
