import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

@tool
def get_products() -> str:
    """
    Return a list of products and their prices.
    Use a database (RAG) in the future
    """
    logger.info("Executing get_products tool.")
    products = "elaichi chai - $16.00, masala chai - $20.00, ginger chai - $15.00, madras coffee - $20.00"
    logger.info(f"Retrieved products: {products}")
    return products

products_tool = get_products