from tools.cart.cart_tool import cart_tools
from langchain.agents import Tool

from tools.product.products_tool import products_tool
from tools.product.summary_tool import generate_summary

from tools.quickbooks.create_invoice_tool import create_invoice_tool
from tools.quickbooks.quickbooks_wrapper import QuickBooksWrapper
from tools.product.summary_tool import generate_summary
from tools.fedex.fedex_tool import create_fedex_shipment as fedex_tool
from tools.paypal.payment_tool import get_paypal_tools, order_tools
from tools.paypal.trigger_payment_tool import trigger_payment_tool

def get_all_tools() -> list:
    return (
        cart_tools
        + [create_invoice_tool, products_tool, fedex_tool, generate_summary, trigger_payment_tool]
        + order_tools
        # + get_paypal_tools()
    )
