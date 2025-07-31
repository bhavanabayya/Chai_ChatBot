from enum import Enum

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
        self.latest_order_text = ""
        self.latest_invoice_id = None
        self.summary_text = ""
        self.order = None
        self.invoice_link = None
        self.venmo_link = "https://venmo.com/chaicompany"
        self.shipping_label = None

    def reset(self):
        self.stage = ChatStage.GREETING
        self.latest_order_text = ""
        self.latest_invoice_id = None
        self.summary_text = ""
        self.order = None
        self.invoice_link = None
        self.shipping_label = None

    def to_dict(self):
        return {
            "stage": self.stage.name,
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
        instance.latest_order_text = data.get("latest_order_text", "")
        instance.latest_invoice_id = data.get("latest_invoice_id", None)
        instance.summary_text = data.get("summary_text", "")
        instance.order = data.get("order")
        instance.invoice_link = data.get("invoice_link")
        instance.shipping_label = data.get("shipping_label")
        return instance
