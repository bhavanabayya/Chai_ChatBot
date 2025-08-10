from enum import Enum
import streamlit as st  # ✅ centralize access here

SESSION_KEY = "chat_state"

class ChatStage(Enum):
    GREETING = "greeting"
    ORDER_SUMMARY = "order_summary"
    AWAITING_INVOICE_CONFIRMATION = "awaiting_invoice_confirmation"
    INVOICE_GENERATED = "invoice_generated"
    AWAITING_PAYMENT_CONFIRMATION = "awaiting_payment_confirmation"
    ORDER_UPDATED = "order_updated"
    COMPLETED = "completed"

class ChatState:
    def __init__(self):
        self.stage = ChatStage.GREETING
        self.customer_id = None
        self.is_guest = False              # ✅ added
        self.latest_order_text = ""
        self.latest_invoice_id = None
        self.summary_text = ""
        self.order = None
        self.invoice_link = None
        self.venmo_link = "https://venmo.com/chaicompany"
        self.shipping_label = None

    def reset(self):
        self.stage = ChatStage.GREETING
        self.customer_id = None
        self.is_guest = False              # ✅ reset
        self.latest_order_text = ""
        self.latest_invoice_id = None
        self.summary_text = ""
        self.order = None
        self.invoice_link = None
        self.shipping_label = None

    def to_dict(self):
        return {
            "stage": self.stage.name,
            "customer_id": self.customer_id,
            "is_guest": self.is_guest,     # ✅ include
            "latest_order_text": self.latest_order_text,
            "latest_invoice_id": self.latest_invoice_id,
            "summary_text": self.summary_text,
            "order": self.order,
            "invoice_link": self.invoice_link,
            "venmo_link": self.venmo_link,
            "shipping_label": self.shipping_label
        }

    @classmethod
    def from_dict(cls, data):
        instance = cls()
        instance.stage = ChatStage[data.get("stage", "GREETING")]
        instance.customer_id = data.get("customer_id")
        instance.is_guest = bool(data.get("is_guest", False))  # ✅ load
        instance.latest_order_text = data.get("latest_order_text", "")
        instance.latest_invoice_id = data.get("latest_invoice_id", None)
        instance.summary_text = data.get("summary_text", "")
        instance.order = data.get("order")
        instance.invoice_link = data.get("invoice_link")
        instance.shipping_label = data.get("shipping_label")
        return instance


# ---------- Centralized helpers (use these everywhere) ----------

def get_state() -> ChatState:
    """Fetch the singleton ChatState from Streamlit session."""
    if SESSION_KEY not in st.session_state:
        st.session_state[SESSION_KEY] = ChatState()
    raw = st.session_state[SESSION_KEY]
    if isinstance(raw, dict):
        st.session_state[SESSION_KEY] = ChatState.from_dict(raw)
    return st.session_state[SESSION_KEY]

def save_state(state: ChatState) -> None:
    """Persist current ChatState back to session."""
    st.session_state[SESSION_KEY] = state

def set_customer(customer_id: str | None, *, is_guest: bool | None = None) -> None:
    s = get_state()
    s.customer_id = customer_id
    if is_guest is not None:
        s.is_guest = is_guest
    save_state(s)

def mark_guest() -> None:
    s = get_state()
    s.is_guest = True
    save_state(s)

def promote_to_real() -> None:
    s = get_state()
    s.is_guest = False
    save_state(s)
