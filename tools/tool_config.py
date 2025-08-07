from tools.cart.cart_tool import cart_tools
from tools.cart.finalize_tool import finalize_order_tool
from langchain.agents import Tool

from tools.product.products_tool import products_tool
from tools.product.summary_tool import generate_summary

from tools.quickbooks.create_invoice_tool import create_invoice_tool
from tools.quickbooks.quickbooks_wrapper import QuickBooksWrapper
from tools.cart.finalize_tool import finalize_order_tool
from tools.product.summary_tool import generate_summary
from tools.fedex.fedex_tool import create_fedex_shipment as fedex_tool
from tools.gmail_tool import gmail_tool
from tools.calendar_tool import calendar_tool
from tools.paypal.payment_tool import get_paypal_tools, order_tools

def get_all_tools() -> list[Tool]:
    return (
        cart_tools
        + [create_invoice_tool, products_tool, fedex_tool, calendar_tool, gmail_tool, finalize_order_tool, generate_summary]
        + order_tools
        + get_paypal_tools()
    )
