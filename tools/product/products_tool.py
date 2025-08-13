from langchain_core.tools import tool

@tool
def get_products() -> str:
    """
    Return a list of products and their prices.
    Use a database (RAG) in the future
    """
    
    return f"elaichi chai - $16.00, masala chai - $20.00, ginger chai - $15.00, madras coffee - $20.00"

products_tool = get_products