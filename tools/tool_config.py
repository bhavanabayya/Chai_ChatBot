from langchain.agents import Tool

# from tools.intuit_tool import intuit_tool
# from tools.venmo_tool import venmo_tool
from tools.cart_tool import cart_tools
from tools.create_invoice_tool import invoice_tool
from tools.fedex_tool import fedex_tool
from tools.calendar_tool import calendar_tool
from tools.gmail_tool import gmail_tool
from tools.calendar_tool import calendar_tool
from tools.payment_tool import get_paypal_tools
from tools.products_tool import products_tool

def get_all_tools() -> list[Tool]:
    return cart_tools + [invoice_tool, products_tool, fedex_tool, calendar_tool, gmail_tool] + get_paypal_tools()
