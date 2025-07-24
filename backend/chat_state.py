from enum import Enum, auto

# class ChatStage(Enum):
#     GREETING = auto()
#     ORDER_TAKING = auto() 
#     AWAITING_ORDER = auto()
#     INVOICE_SENT = auto()
#     AWAITING_CONFIRMATION = auto()
#     PAYMENT_LINK_SENT = auto()
#     PAYMENT_CONFIRMED = auto()
#     SHIPPING_LABEL_SENT = auto()
class ChatStage(Enum):
    GREETING = auto()
    AWAITING_ORDER = auto()
    INVOICE_SENT = auto()
    PAYMENT_LINK_SENT = auto()
    PAYMENT_CONFIRMED = auto()
    SHIPPING_LABEL_SENT = auto()

class ChatState:
    def __init__(self):
        self.stage = ChatStage.GREETING
        self.order = None
        self.invoice_link = None
        self.venmo_link = "https://venmo.com/chaicompany"
        self.shipping_label = None

    def reset(self):
        self.stage = ChatStage.GREETING
        self.order = None
        self.invoice_link = None
        self.shipping_label = None

    def to_dict(self):
        return {
            "stage": self.stage.name,
            "order": self.order,
            "invoice_link": self.invoice_link,
            "venmo_link": self.venmo_link,
            "shipping_label": self.shipping_label
        }

    @classmethod
    def from_dict(cls, data):
        instance = cls()
        instance.stage = ChatStage[data.get("stage", "GREETING")]
        instance.order = data.get("order")
        instance.invoice_link = data.get("invoice_link")
        instance.shipping_label = data.get("shipping_label")
        return instance
