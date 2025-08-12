import os
import sys
import io
from pydantic import BaseModel
import requests
from pathlib import Path
from functools import partial

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool

from typing import List
from tools.tool_config import get_all_tools
from tools.quickbooks.quickbooks_wrapper import QuickBooksWrapper

from tools.cart.cart_tool import (
    get_cart_for_session,
    add_to_cart,
    remove_from_cart,
    view_cart,
    clear_cart
)

# --- Environment and App Setup ---

# Load environment variables
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL")

# Initialize FastAPI app
app = FastAPI()

# Define allowed origins for CORS
# Your React/TypeScript frontend will likely be on localhost:3000
origins = [
    "http://localhost:8080",
    # "http://localhost:5173", # Common for Vite projects
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PDF Download Endpoints ---

# Initialize QuickBooks wrapper
qb = QuickBooksWrapper()

@app.get("/download/invoice/{invoice_id}")
def download_invoice(invoice_id: str):
    try:
        pdf_bytes = qb.get_invoice_pdf(invoice_id)
        return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers={
            "Content-Disposition": f"attachment; filename=invoice_{invoice_id}.pdf"
        })
    except Exception as e:
        return {"error": str(e)}

# --- Cart Tool Creation ---
# def get_session_specific_cart_tools(session_id: str) -> list:
#     """Creates tool instances that are bound to a specific session's cart."""
#     # Get the specific cart for this session
#     cart = get_cart_for_session(session_id)

#     # Create a list of Tool objects, using partial to bind the session's cart
#     # to the first argument of each cart function.
#     session_tools = [
#         Tool(
#             name="add_to_cart",
#             func=partial(add_to_cart, cart),
#             description="Adds a specified quantity of an item to the shopping cart."
#         ),
#         Tool(
#             name="remove_from_cart",
#             func=partial(remove_from_cart, cart),
#             description="Removes a specified quantity of an item from the shopping cart."
#         ),
#         Tool(
#             name="view_cart",
#             func=partial(view_cart, cart),
#             description="Displays the current contents of the shopping cart."
#         ),
#         Tool(
#             name="clear_cart",
#             func=partial(clear_cart, cart),
#             description="Empties the shopping cart."
#         ),
#     ]
#     return session_tools


# --- Session and Memory Management ---

# This dictionary will store memory objects, with session IDs as keys.
# WARNING: This is an in-memory store. It will be cleared if the server restarts.
session_memories = {}

def get_memory_for_session(session_id: str) -> ConversationBufferMemory:
    """Retrieves or creates a memory object for a given session ID."""
    if session_id not in session_memories:
        # Ensure new memory objects are created with the correct configuration
        session_memories[session_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    return session_memories[session_id]

# --- LangChain Agent Creation (Refactored) ---

def create_agent_executor(memory: ConversationBufferMemory) -> AgentExecutor:
    """
    Creates and returns the LangChain agent executor for a given memory instance.
    """
    tools = get_all_tools()

    llm = ChatOpenAI(
        model=OPENAI_API_MODEL,
        temperature=0,
        openai_api_key=OPENAI_API_KEY
    )

    SYSTEM_PROMPT = """
        You are a friendly and helpful AI assistant for an e-commerce business called Chai Corner.
        Your job is to guide customers through:
        - viewing products,
        - placing an order,
        - getting an invoice,
        - making payment,
        - receiving a shipping label.
        Here are the tools you have access to:
        {{tools}}
        **Conversation Flow to Follow**:
        1. Greet the user and ask how you can help.
        2. If the user asks about products or menu, use `products_tool` to show item names and prices.
        3. If the user wants to order items, use the `add_to_cart`, `view_cart`, `clear_cart`, and `remove_from_cart` tools to manage their cart.
        6. Ask the user if they want to proceed to payment. If yes, use the `paypal` tool to generate a payment link.
        7. Once confirmed, use a tool from the PayPal toolkit to generate a payment link for the order. Use order tools to keep track of order ID.
        8. Once the customer says that they have paid, use the order number to confirm that they have indeed done so. Output the details to the customer
        9. Then use the `create_fedex_shipment` tool to generate tracking number and label URL. Display it to the customer. Clear cart.
        Always follow these steps in order. Never skip steps. Confirm with the user at each stage.
    """
    
    
        # 4. Generate an invoice and give the pdf to the customer for customer 58 using `invoice_tool`.
        # *(Use the format: 'Generate 2 Madras Coffee and 1 Cardamom Chai for customer 58' to interface with the tool).*
        # Let the customer verify everything is correct.
        # 5. After invoice generation, show the invoice link using:
        # **http://localhost:8001/download/invoice/{{invoice_id}}**

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
        memory=memory,  # Inject the session-specific memory here
        verbose=True,
        handle_parsing_errors=True
    )

    return agent_executor

# --- Main Chat Endpoint ---

class ChatRequest(BaseModel):
    message: str
    session_id: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Receives a message, retrieves the correct session memory,
    creates an agent with that memory, and returns a response.
    """
    try:
        session_id = request.session_id
        
        # 1. Get session-specific memory and cart tools
        memory = get_memory_for_session(session_id)
        # session_cart_tools = get_session_specific_cart_tools(session_id)
        
        # 2. Combine with any static, non-session tools
        # all_tools_for_session = session_cart_tools + get_all_tools()

        # 3. Create an agent executor with the combined, session-specific toolset
        agent_executor = create_agent_executor(memory)

        # 4. Invoke the agent
        response = await agent_executor.ainvoke({"input": request.message})

        return {"response": response.get("output")}

    except Exception as e:
        # Log the error for debugging
        print(f"An error occurred in chat endpoint: {e}")
        return {"error": "An internal server error occurred."}



### Payment websocket connection
class ConnectionManager:
    """Manages active WebSocket connections."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_json_to_client(self, data: dict, websocket: WebSocket):
        """Sends a JSON message to a specific client."""
        await websocket.send_json(data)

manager = ConnectionManager()

