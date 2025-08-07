import os
import sys
import io
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from tools.quickbooks_wrapper import QuickBooksWrapper
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pathlib import Path

from tools.tool_config import get_all_tools

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL")

# Initialize FastAPI app
app = FastAPI()

# Initialize QuickBooks wrapper
qb = QuickBooksWrapper()

# Endpoint to download invoice PDF
@app.get("/download/invoice/{invoice_id}")
def download_invoice(invoice_id: str):
    try:
        pdf_bytes = qb.get_invoice_pdf(invoice_id)
        return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers={
            "Content-Disposition": f"attachment; filename=invoice_{invoice_id}.pdf"
        })
    except Exception as e:
        return {"error": str(e)}


# Create the Langchain Agent
def create_agent():
    """
    Creates and returns the Langchain agent executor.
    This function should only be called ONCE per user session.
    Its state (including memory) is maintained by Streamlit's session_state.
    """
    
    # Get all the tools that are available for the agent to use:
    tools = get_all_tools()
        
    # Define the LLM to be used by the agent
    # Keep temperature at 0 to keep responses to reduce randomness
    # gpt-4o vs gpt-4-turbo: gpt-4o is faster and cheaper (twice as fast, half as expensive)
    llm = ChatOpenAI(
        model = OPENAI_API_MODEL,
        temperature = 0,
        openai_api_key = OPENAI_API_KEY
    )

    memory = ConversationBufferMemory(
        memory_key="chat_history", 
        return_messages=True
    )

    # Define the prompt. Outline behaviour and tools.
    # TODO: Improve this. Correct tool names.
    SYSTEM_PROMPT = """
    You are a friendly and helpful AI assistant for an e-commerce business called Chai Corner.
    Your goal is to help customers find products, add them to a cart, and complete their purchase.
    Be conversational and guide the user step-by-step. Do not make up product IDs or prices. Only use the information provided by the tools.

    Here are the tools you have access to:
    {{tools}}

    Follow this process:
    1. Greet the user and ask for their full name (e.g., "John Doe").
    2. Use the validate_customer_tool immediately to check if the customer exists using DisplayName in QuickBooks.
         - If the customer exists, greet them with "Welcome back, [name]!" and continue.
         - If the customer does not exist, ask “Would you like to continue as a guest?”
                - If yes, create a guest profile using create_guest_tool and let them know: "Nice to meet you! We've created a guest profile for now."
    3. If the user asks about products, use products_tool.
    4. Use the cart tools when user wants to add or remove items from their order, view cart and clear cart.
    5. Generate an invoice and give the pdf to the customer with corresponding customer_id using create_invoice_tool (Use the format: 'Generate 2 Madras Coffee and 1 Cardamom Chai for customer' to interface with the tool). Let the customer verify everything is correct.
    6. Once confirmed, use a tool from the PayPal toolkit to generate a payment link for the order. Use order tools to keep track of order ID.
    7. Once the customer says that they have paid, use the order number to confirm that they have indeed done so. Output the details to the customer
    8. After the order is finalized using FinalizeOrder, use the 'create_fedex_shipment' from fedex_tool to create a shipment for the order and display the tracking number and label URL..    
    9.If the customer was initially added as a guest, ask: "Would you like to save your profile for future orders?"
        - If the customer says yes AND the variable is_guest is True:
            1. Prompt the user to provide their full details including:
                - First name
                - Last name
                - Phone number
                - Email address
                - Shipping address (street, city, state, postal code)

            2. Once all details are received, use the rename_customer_tool with:
                - customer_id
                - new_name (first + last name)
                - phone
                - email
                - address_line1
                - city
                - state
                - postal_code

            """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"), # This is where the agent's thought process will be injected
        ]
    )

    # Use models that natively output structured tool calls (JSON)
    # More reliable evolution of the ReAct pattern
    agent = create_tool_calling_agent(llm, tools, prompt)
    

    # This is the runnable that will execute the agent's decisions.
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        memory=memory, 
        verbose=True, 
        handle_parsing_errors=True
    )

    return agent_executor
