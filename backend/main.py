import os
import io
import sys
import logging
from pathlib import Path
import requests
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Routers
from routers.fedex import router as fedex_router
from routers.paypal import router as paypal_router
from routers.quickbooks import router as quickbooks_router
from routers.customer import router as customer_router
from routers.applepay import router as applepay_router

# Tools & SDKs
from state.session import set_websocket
from tools.tool_config import get_all_tools
from tools.quickbooks.quickbooks_wrapper import QuickBooksWrapper

# ──────────────────────────────────────────────────────────────────────────────
# Set up logging for the application
# ──────────────────────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, # Set the lowest level of message to display
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout, # Ensure logs go to the terminal
)
logger.info("Chai Corner Backend starting up...")

# ──────────────────────────────────────────────────────────────────────────────
# Environment
# ──────────────────────────────────────────────────────────────────────────────
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL") or "gpt-4o-mini"  # safe default

if not OPENAI_API_KEY:
    logger.critical("Missing OPENAI_API_KEY in environment. Shutting down.")
    raise RuntimeError("Missing OPENAI_API_KEY in environment.")
else:
    logger.info("OpenAI API key loaded.")

# ──────────────────────────────────────────────────────────────────────────────
# FastAPI app
# ──────────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Chai Corner Backend")

# Define allowed origins for CORS
origins = [
    "http://10.0.0.80:8080",
    "http://localhost:8080",
    "http://localhost:5173",
    "http://127.0.0.1:8080",
    "http://10.0.0.106:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize SDK wrappers once
try:
    qb = QuickBooksWrapper()
    logger.info("QuickBooksWrapper initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize QuickBooksWrapper: {e}", exc_info=True)
    qb = None

# Health
@app.get("/health")
def health():
    logger.info("Health check endpoint called.")
    return {"status": "ok"}

# ──────────────────────────────────────────────────────────────────────────────
# Downloads
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/download/invoice/{invoice_id}")
def download_invoice(invoice_id: str):
    """Stream a QuickBooks invoice PDF by invoice_id."""
    logger.info(f"Received request to download invoice: {invoice_id}")
    if not qb:
        logger.error("QuickBooksWrapper is not initialized. Cannot download invoice.")
        return JSONResponse(status_code=500, content={"error": "Internal service error. QuickBooks not configured."})
        
    try:
        pdf_bytes = qb.get_invoice_pdf(invoice_id)
        logger.info(f"Successfully retrieved PDF for invoice: {invoice_id}")
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=invoice_{invoice_id}.pdf"},
        )
    except Exception as e:
        logger.error(f"Failed to download invoice {invoice_id}. Error: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/download/label/{tracking_number}")
def download_label(tracking_number: str):
    """
    Streams the FedEx label PDF given a tracking number.
    NOTE: Replace the URL logic with your persisted label lookup if available.
    """
    logger.info(f"Received request to download FedEx label for tracking number: {tracking_number}")
    try:
        label_url = f"https://www.fedex.com/label/{tracking_number}.pdf"
        resp = requests.get(label_url, timeout=20)
        if resp.status_code != 200:
            logger.error(f"Failed to fetch label from FedEx. Status code: {resp.status_code}")
            return JSONResponse(
                status_code=resp.status_code,
                content={"error": f"Failed to fetch label: {resp.status_code}"},
            )
        logger.info("Successfully fetched FedEx label.")
        return StreamingResponse(
            io.BytesIO(resp.content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=label_{tracking_number}.pdf"},
        )
    except Exception as e:
        logger.error(f"An error occurred while downloading label: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})

# ──────────────────────────────────────────────────────────────────────────────
# Agent
# ──────────────────────────────────────────────────────────────────────────────

# Session and Memory Management

# This dictionary will store memory objects, with session IDs as keys.
# WARNING: This is an in-memory store. It will be cleared if the server restarts.
session_memories = {}

def get_memory_for_session(session_id: str) -> ConversationBufferMemory:
    """Retrieves or creates a memory object for a given session ID."""
    if session_id not in session_memories:
        logger.info(f"No memory found for session {session_id}. Creating a new one.")
        session_memories[session_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        session_memories[session_id].chat_memory.add_ai_message(f"Session ID: {session_id}")
    return session_memories[session_id]


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(ws: WebSocket, session_id: str):
    logger.info(f"New WebSocket connection established for session ID: {session_id}")

    await ws.accept()
    set_websocket(session_id, ws)
    
    try:
        while True:
            data = await ws.receive_json()
            logger.info(f"Websocket: Message from {session_id}: {data}")
            
            if data.get("event") == "payment_complete":
                logging.info(f"Payment complete event received for session: {session_id}")
                
                memory = get_memory_for_session(session_id)
                agent_executor = create_agent(memory)
                response = await agent_executor.ainvoke({"input": "The payment has been verified. Please move on to shipping."})
                
                logging.info(f"Sending response back after payment: {response.get('output')}")
                await ws.send_json({
                    "type": "agent_message",
                    "ai_message": response.get("output")
                })
    except Exception as e:
        logger.error(f"WebSocket connection closed for session {session_id}. Error: {e}", exc_info=True)
        set_websocket(session_id, None)

def create_agent(memory: ConversationBufferMemory) -> AgentExecutor:
    """Create and return the LangChain tool-calling agent executor."""
    tools = get_all_tools()
    logger.debug(f"Loaded {len(tools)} tools for the agent.")

    llm = ChatOpenAI(
        model=OPENAI_API_MODEL,
        temperature=0,
        openai_api_key=OPENAI_API_KEY,
    )
    
    SYSTEM_PROMPT = """
        You are a friendly and helpful AI assistant for an e-commerce business called Chai Corner.
        Your goal is to help customers find products, add them to a cart, and complete their purchase.
        Be conversational and guide the user step-by-step. Do not make up product IDs or prices. Only use the information provided by the tools. Do not use markdown (ie. ** to bold) at any point in this conversation.

        Here are the tools you have access to:
        {{tools}}

        Follow this process:
        1. Greet the user. Ask for their full name if they are a returning customer (e.g., "John Doe"), or if they'd like to continue as guest.
            - If the customer provides their name, use the validate_customer_tool immediately to check if the customer exists using DisplayName in QuickBooks.
                - If the customer exists, greet them with "Welcome back, [name]!" and continue.
                - If the customer does not exist, ask: 
                    “I couldn’t find your profile. Would you like to continue as a guest?”
            - If the user chooses to continue as guest, create a guest profile using `create_guest_tool`, and let them know: "Nice to meet you! We've created a guest profile for now."
        2. If the user asks about products, use `products_tool`. 
        3. When adding items to the cart, use `products_tool` to make sure they are a valid item and then add to cart using `add_to_cart` tool. Use the other cart tools to remove items, view cart and clear cart.
        4. Generate an invoice using create_invoice_tool. Send the link to the customer. Let the Customer verify that everything is correct.
        5. If the user wants to proceed, you must use `view_cart` tool and `generate_summary` tool to provide cart_items to `trigger_payment_tool` tool.
        6. If the user claims to have paid, use `stripe_checkout_status_tool` tool to see if payment has been made. DO NOT move on to the next step if the payment has not been made. Let customer know they still have to pay if that is the case.
        7. Once Payment is complete, use `fedex_tool` tool and return the tracking ID and the link to the shipping label.
        8. (Mandatory) DO NOT forget to ask if and only if the customer was initially added as a guest:
            - Only ask: "Would you like to save your profile for future orders?"
            - If they say yes:
                1) Prompt the user to provide their full details:
                    - First name
                    - Last name
                    - Phone number
                    - Email address
                    - Shipping address (street, city, state, postal code)
                2) After all details are collected, call rename_customer_tool with:
                    - customer_id
                    - new_name (first + last)
                    - phone
                    - email
                    - address_line1
                    - city
                    - state
                    - postal_code
            - Only ask the save-profile question if and only if the latest client state says is_guest == True (passed via the input string).
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    agent = create_tool_calling_agent(llm, tools, prompt)
    logger.info("LangChain agent created.")

    return AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
    )
    
# ──────────────────────────────────────────────────────────────────────────────
# Main chat endpoint
# ──────────────────────────────────────────────────────────────────────────────

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
        logger.info(f"Received chat request for session ID: {session_id}")
        
        memory = get_memory_for_session(session_id)
        
        agent_executor = create_agent(memory)

        response = await agent_executor.ainvoke({"input": request.message})
        logger.info(f"Agent response for session {session_id} is ready.")

        return {"response": response.get("output")}

    except Exception as e:
        logger.error(f"An error occurred in chat endpoint for session {session_id}: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": "An internal server error occurred."})



# ──────────────────────────────────────────────────────────────────────────────
# Routers
# ──────────────────────────────────────────────────────────────────────────────
app.include_router(applepay_router)
app.include_router(customer_router)
app.include_router(quickbooks_router)
app.include_router(paypal_router)
app.include_router(fedex_router)
