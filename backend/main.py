import os
import sys
import io
import requests
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tools.tool_config import get_all_tools
from tools.quickbooks.quickbooks_wrapper import QuickBooksWrapper
from tools.fedex.fedex_api_wrapper import FedExWrapper 

# Load environment variables
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL")

# Initialize FastAPI app
app = FastAPI()

# Initialize QuickBooks wrapper
qb = QuickBooksWrapper()

#  INVOICE PDF Download Endpoint
@app.get("/download/invoice/{invoice_id}")
def download_invoice(invoice_id: str):
    try:
        pdf_bytes = qb.get_invoice_pdf(invoice_id)
        return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers={
            "Content-Disposition": f"attachment; filename=invoice_{invoice_id}.pdf"
        })
    except Exception as e:
        return {"error": str(e)}

#  FEDEX LABEL Download Endpoint (BONUS)
@app.get("/download/label/{tracking_number}")
def download_label(tracking_number: str):
    """
    Streams the FedEx label PDF given a tracking number.
    This assumes the label URL is standard format.
    """
    try:
        # You can enhance this to look up from saved label store if needed
        label_url = f"https://www.fedex.com/label/{tracking_number}.pdf"  # or from DB if persisted
        response = requests.get(label_url)

        if response.status_code != 200:
            return {"error": f"Failed to fetch label: {response.status_code}"}

        return StreamingResponse(io.BytesIO(response.content), media_type="application/pdf", headers={
            "Content-Disposition": f"attachment; filename=label_{tracking_number}.pdf"
        })
    except Exception as e:
        return {"error": str(e)}

#  LangChain Agent Creation
def create_agent():
    """
    Creates and returns the LangChain agent executor.
    """
    tools = get_all_tools()

    llm = ChatOpenAI(
        model=OPENAI_API_MODEL,
        temperature=0,
        openai_api_key=OPENAI_API_KEY
    )

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )

    SYSTEM_PROMPT = """
        
        You are a friendly and helpful AI assistant for an e-commerce business called Chai Corner.

        Your job is to guide customers through:
        - viewing products,
        - placing an order,
        - getting an invoice,
        - making payment,
        - receiving shipping label.

        Here are the tools you have access to:
        {{tools}}

        **Conversation Flow to Follow**:

        1. Greet the user and ask how you can help.
        2. If the user asks about products or menu, use `products_tool` to show item names and prices.
        3. If the user wants to order items, use the `add_to_cart`, `view_cart`, and `remove_from_cart` tools from `cart_tools` to manage their cart.
        4. Generate an invoice and give the pdf to the customer for customer 58 using `invoice_tool`.  
        *(Use the format: 'Generate 2 Madras Coffee and 1 Cardamom Chai for customer 58' to interface with the tool).*  
        Let the customer verify everything is correct.
        5. After invoice generation, show the invoice link using:  
        **http://localhost:8001/download/invoice/{{invoice_id}}**
        6. Ask the user if they want to proceed to payment. If yes, use the `paypal` tool to generate a payment link.
        7. Once the customer confirms the payment, use the `finalize_order_tool` to mark the order complete.
        8. Then use the `create_fedex_shipment` tool to generate tracking number and label URL. Display it to the customer.

        Always follow these steps in order. Never skip steps. Confirm with the user at each stage.
"""

        


    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)

    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        memory=memory, 
        verbose=True, 
        handle_parsing_errors=True
    )

    return agent_executor
