# tools/finalize_tool.py

from langchain_core.tools import tool

@tool
def finalize_order(_: str = "") -> str:
    """
    Marks the order as finalized after payment.
    """
    return " Your order has been finalized and will be processed shortly."


finalize_order_tool = finalize_order
