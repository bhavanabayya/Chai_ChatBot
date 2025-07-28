from langchain_core.tools import tool

@tool
def get_products() -> str:
    """
    Return a list of products and their prices.
    Use a database (RAG)
    """
    
    return f"Chai - $1.50, coffee - $2"

products_tool = get_products
