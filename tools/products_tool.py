from langchain_core.tools import tool

@tool
def get_products() -> str:
    """
    Return a list of products and their prices.
    Use a database (RAG) in the future
    """
    
    return f"elaichi chai - $1.50, masala chai - $1.50, ginger chai - $1.75, madras coffee - $2.00"

products_tool = get_products