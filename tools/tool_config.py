from langchain.agents import Tool

from tools.cart.cart_tool import cart_tools
from tools.cart.finalize_tool import finalize_order_tool

from tools.customer.create_customer_tool import create_customer_tool
from tools.customer.create_guest_tool import create_guest_tool
from tools.customer.rename_customer_tool import rename_customer_tool
from tools.customer.validate_customer_tool import validate_customer_tool

from tools.product.products_tool import products_tool
from tools.product.summary_tool import generate_summary

from tools.applepay.apple_pay_tool import apple_pay_tools
from tools.quickbooks.create_invoice_tool import create_invoice_tool
from tools.fedex.fedex_tool import create_fedex_shipment as fedex_tool

from tools.gmail_tool import gmail_tool
from tools.calendar_tool import calendar_tool

from tools.paypal.payment_tool import get_paypal_tools, order_tools

def get_all_tools() -> list[Tool]:
    return (
        cart_tools
        + [
            create_invoice_tool,
            products_tool,
            fedex_tool,
            create_customer_tool,
            create_guest_tool,
            rename_customer_tool,
            validate_customer_tool,
            calendar_tool,
            gmail_tool,
            finalize_order_tool,
            generate_summary,
        ]
        + order_tools
        + apple_pay_tools
        + get_paypal_tools()
    )
