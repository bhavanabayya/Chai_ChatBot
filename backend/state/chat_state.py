import logging

logger = logging.getLogger(__name__)

class ChatState:
    
    def __init__(self):
        self.customer_id = None
        self.is_guest = False
        self.cart = {}
        self.websocket = None
        self.stripe_order_id = None
        self.paypal_order_id = None
        logger.info("New ChatState object initialized.")

    def reset(self):
        logger.info(f"Resetting state for ChatState object with customer_id: {self.customer_id}")
        self.customer_id = None
        self.is_guest = False
        self.cart = {}
        self.websocket = None
        self.stripe_order_id = None
        self.paypal_order_id = None
        logger.info("ChatState object successfully reset.")
        
    def to_dict(self):
        logger.debug("Converting ChatState object to dictionary.")
        return {
            "customer_id": self.customer_id,
            "is_guest": self.is_guest,
            "cart": self.cart,
            "websocket": self.websocket,
            "stripe_order_id": self.stripe_order_id,
            "paypal_order_id": self.paypal_order_id
        }

    @classmethod
    def from_dict(cls, data):
        logger.info(f"Creating ChatState object from dictionary data.")
        instance = cls()
        instance.customer_id = data.get("customer_id")
        instance.is_guest = bool(data.get("is_guest", False))
        instance.cart = data.get("cart")
        instance.websocket = data.get("websocket")
        instance.stripe_order_id = data.get("stripe_order_id")
        instance.paypal_order_id = data.get("paypal_order_id")
        logger.debug(f"ChatState object created with customer_id: {instance.customer_id}")
        return instance