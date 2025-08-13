import os
import sys
import io
from pathlib import Path
from functools import partial
from pydantic import BaseModel, create_model
from dotenv import load_dotenv


from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool

from tools.tool_config import get_all_tools
from tools.quickbooks.quickbooks_wrapper import QuickBooksWrapper
from tools.paypal.trigger_payment_tool import session_active_websockets 

# --- Environment and App Setup ---

# Load environment variables
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL")

# Initialize FastAPI app
app = FastAPI()

# Define allowed origins for CORS
origins = [
    "http://10.0.0.80:8080",
    "http://localhost:8080",
    "http://localhost:5173",
    "http://127.0.0.1:8080",
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


# --- Session and Memory Management ---

# This dictionary will store memory objects, with session IDs as keys.
# WARNING: This is an in-memory store. It will be cleared if the server restarts.
from typing import Dict
session_memories = {}

def get_memory_for_session(session_id: str) -> ConversationBufferMemory:
    """Retrieves or creates a memory object for a given session ID."""
    if session_id not in session_memories:
        # Ensure new memory objects are created with the correct configuration
        session_memories[session_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        session_memories[session_id].chat_memory.add_ai_message(f"Session ID: {session_id}")
    return session_memories[session_id]


import logging
logging.basicConfig(
    level=logging.INFO, # Set the lowest level of message to display
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout, # Ensure logs go to the terminal
)

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(ws: WebSocket, session_id: str):
    await ws.accept()
    session_active_websockets[session_id] = ws
    logging.info(f"Session_id in main.websocket_endpoint: {session_id}")
    try:
        while True:
            data = await ws.receive_json()
            print(f"Message from {session_id}: {data}")
    except Exception:
        session_active_websockets.pop(session_id, None)
        
import inspect

def create_agent_executor(memory: ConversationBufferMemory, session_id: str) -> AgentExecutor:
    """
    Creates and returns the LangChain agent executor for a given memory instance.
    """
    base_tools = get_all_tools()
    
    logging.info(f"Session_id in main.create_agent_executor: {session_id}")

    llm = ChatOpenAI(
        model=OPENAI_API_MODEL,
        temperature=0,
        openai_api_key=OPENAI_API_KEY
    )

    # 👇 Simplified the prompt. The agent no longer needs to worry about the session_id.
    SYSTEM_PROMPT = """
        You are a friendly and helpful AI assistant for an e-commerce business called Chai Corner.
        Your job is to guide customers through viewing products and placing an order.
        Here are the tools you have access to:
        {{tools}}
        **Conversation Flow to Follow**:
        1. Greet the user and ask how you can help.
        2. If the user asks about products or menu, use `products_tool` to show item names and prices.
        3. Use the `add_to_cart`, `view_cart`, `clear_cart`, and `remove_from_cart` tools to manage the user's cart.
        4. Ask the user if they want to proceed to payment. If yes, call the `trigger_payment_tool` for which you MUST provide the cart_items data using the `view_cart` and `products_tool` tools.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, base_tools, prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=base_tools,
        memory=memory,
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
        
        memory = get_memory_for_session(session_id)
        
        logging.info(f"Session_id in main.chat_endpoint: {session_id}")

        agent_executor = create_agent_executor(memory, session_id)

        response = await agent_executor.ainvoke({"input": request.message})

        return {"response": response.get("output")}

    except Exception as e:
        print(f"An error occurred in chat endpoint: {e}")
        return {"error": "An internal server error occurred."}

