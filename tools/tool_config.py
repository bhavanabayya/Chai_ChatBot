from langchain.agents import Tool

from tools.cart_tool import cart_tools
# from tools.create_invoice_tool import invoice_tool
from tools.create_invoice_tool import create_invoice_tool
# from tools.fedex_tool import fedex_tool
from tools.fedex_tool import create_fedex_shipment as fedex_tool
from tools.calendar_tool import calendar_tool
from tools.gmail_tool import gmail_tool
from tools.calendar_tool import calendar_tool
from tools.payment_tool import get_paypal_tools, order_tools
from tools.products_tool import products_tool
from tools.validate_customer_tool import validate_customer_tool
from tools.create_guest_tool import create_guest_tool
from tools.rename_customer_tool import rename_customer_tool

def get_all_tools() -> list[Tool]:
    return cart_tools + [create_invoice_tool,  validate_customer_tool, create_guest_tool, rename_customer_tool, products_tool, fedex_tool, calendar_tool, gmail_tool] + order_tools + get_paypal_tools()
