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
    Your goal is to help customers find products, add them to a cart, and complete their purchase.
    Be conversational and guide the user step-by-step. Do not make up product IDs or prices. Only use the information provided by the tools.

    Here are the tools you have access to:
    {{tools}}

    Follow this process:
    1. Greet the user and ask how you can help.
    2. If the user asks about products, use products_tool.
    3. Use the cart tools when user wants to add or remove items from their order, view cart and clear cart.
    4. Generate an invoice and give the pdf to the customer for customer 58 using invoice_tool.
    5. Once confirmed, use a tool from the PayPal toolkit to generate a payment link for the order.
    6. Once the customer says they have paid, finalize the order.
    7. Then, use the FedEx shipment tool to generate a tracking number and label URL.    
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
