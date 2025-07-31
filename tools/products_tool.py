from langchain_core.tools import tool

@tool
def get_products() -> str:
    """
    Return a list of products and their prices.
    Use a database (RAG) in the future
    """
    
    return f"elaichi chai - $16, masala chai - $20, ginger chai - $15, madras coffee - $20"

products_tool = get_products