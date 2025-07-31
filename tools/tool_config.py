from langchain.agents import Tool

from tools.create_invoice import create_invoice_tool
from tools.products_tool import products_tool
from tools.payment_tool import get_paypal_tools
from tools.fedex_tool import fedex_tool
from tools.calendar_tool import calendar_tool
from tools.add_to_cart_tool import add_to_cart_tool
from tools.view_cart_tool import view_cart_tool
from tools.finalize_tool import finalize_order_tool

def get_all_tools() -> list[Tool]:
    return [
        products_tool,
        create_invoice_tool,
        add_to_cart_tool,
        view_cart_tool,
        finalize_order_tool,
        fedex_tool,
        calendar_tool,
        *get_paypal_tools()
    ]