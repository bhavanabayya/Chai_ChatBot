import os
import io
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
from backend.routers.fedex import router as fedex_router
from backend.routers.paypal import router as paypal_router
from backend.routers.quickbooks import router as quickbooks_router
from backend.routers.customer import router as customer_router
from backend.routers.applepay import router as applepay_router

# Tools & SDKs
from backend.state.session import set_websocket
from tools.tool_config import get_all_tools
from tools.quickbooks.quickbooks_wrapper import QuickBooksWrapper

# ──────────────────────────────────────────────────────────────────────────────
# Logging. TODO: Disable in prod :)
# ──────────────────────────────────────────────────────────────────────────────
import sys
import logging
logging.basicConfig(
    level=logging.INFO, # Set the lowest level of message to display
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout, # Ensure logs go to the terminal
)

# ──────────────────────────────────────────────────────────────────────────────
# Environment
# ──────────────────────────────────────────────────────────────────────────────
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL") or "gpt-4o-mini"  # safe default

if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY in environment.")

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
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize SDK wrappers once
qb = QuickBooksWrapper()

# Health
@app.get("/health")
def health():
    return {"status": "ok"}

# ──────────────────────────────────────────────────────────────────────────────
# Downloads
# ──────────────────────────────────────────────────────────────────────────────
@app.get("/download/invoice/{invoice_id}")
def download_invoice(invoice_id: str):
    """Stream a QuickBooks invoice PDF by invoice_id."""
    try:
        pdf_bytes = qb.get_invoice_pdf(invoice_id)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=invoice_{invoice_id}.pdf"},
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/download/label/{tracking_number}")
def download_label(tracking_number: str):
    """
    Streams the FedEx label PDF given a tracking number.
    NOTE: Replace the URL logic with your persisted label lookup if available.
    """
    try:
        label_url = f"https://www.fedex.com/label/{tracking_number}.pdf"
        resp = requests.get(label_url, timeout=20)
        if resp.status_code != 200:
            return JSONResponse(
                status_code=resp.status_code,
                content={"error": f"Failed to fetch label: {resp.status_code}"},
            )
        return StreamingResponse(
            io.BytesIO(resp.content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=label_{tracking_number}.pdf"},
        )
    except Exception as e:
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
        # Ensure new memory objects are created with the correct configuration
        session_memories[session_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        session_memories[session_id].chat_memory.add_ai_message(f"Session ID: {session_id}")
    return session_memories[session_id]




@app.websocket("/ws/{session_id}")
async def websocket_endpoint(ws: WebSocket, session_id: str):
    # TODO: Remove later
    logging.info(f"Session_id in main.websocket_endpoint: {session_id}")

    await ws.accept()
    set_websocket(session_id, ws)
    
    try:
        while True:
            data = await ws.receive_json()
            print(f"Websocket --- Message from {session_id}: {data}")
            
            if data.get("event") == "payment_complete":
                #
                #   TODO: Actually make sure it is paid
                #
                logging.info(f"main.py --- Payment complete for session: {session_id}")
                
                memory = get_memory_for_session(session_id)

                agent_executor = create_agent(memory)

                response = await agent_executor.ainvoke({"input": "The payment has been verified. Please move on to shipping."})
                
                logging.info(f"main.py --- Sending response back after payment: {response.get("output")}")
                await ws.send_json({
                    "type": "agent_message",
                    "ai_message": response.get("output")
                })
    except Exception:
        set_websocket(session_id, None)
        

def create_agent(memory: ConversationBufferMemory) -> AgentExecutor:
    """Create and return the LangChain tool-calling agent executor."""
    tools = get_all_tools()

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
        7. Once Payment is complete, use `create_fedex_shipment` tool and return the tracking ID and the link to the shipping label.
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


                        # - Phone number
                        # - Email address
    # 6. ONLY AFTER the customer confirms the invoice is correct and wants to proceed to payment, you MUST provide BOTH payment options:
    #    - FIRST: Use get_products to get the correct prices, then calculate the total amount
    #    - SECOND: Use create_order tool to generate a PayPal payment link with the calculated total amount, then save_order_id to save the PayPal order ID
    #    - THIRD: Use generate_apple_pay_link tool to generate an Apple Pay (Stripe) payment link with the same calculated total amount
    #    - Present both options clearly showing different URLs:
    #      "Here are your payment options:
    #      1. **[Pay with PayPal](PayPal_URL_from_create_order)**
    #      2. **[Pay with Apple Pay](Stripe_URL_from_generate_apple_pay_link)**"
    
    # 7. When checking payment status:
    #    - Check BOTH methods in the same turn:
    #         (a) PayPal: call get_order_id and then get_order_details or capture_order to confirm status.
    #         (b) Apple Pay: call get_apple_pay_session_status with the session_id from the last generated Stripe link.
    #    - If PayPal status is "APPROVED" or "COMPLETED", use create_fedex_shipment and respond with: "✅ Payment received via PayPal! 📦 Shipment has been successfully created! Here are the details:"
    #    - If Apple Pay shows "complete" and "paid" status, use create_fedex_shipment and respond with: "✅ Payment received via Apple Pay! 📦 Shipment has been successfully created! Here are the details:"
    #    - NEVER guess or assume the payment method - ALWAYS use the tools
    #    - MANDATORY: Use the actual tool results to determine payment method, not memory or assumptions

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)

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
        
        memory = get_memory_for_session(session_id)
        
        # TODO: Remove later
        logging.info(f"Session_id in main.chat_endpoint: {session_id}")

        agent_executor = create_agent(memory)

        response = await agent_executor.ainvoke({"input": request.message})

        return {"response": response.get("output")}

    except Exception as e:
        print(f"An error occurred in chat endpoint: {e}")
        return {"error": "An internal server error occurred."}



# ──────────────────────────────────────────────────────────────────────────────
# Routers
# ──────────────────────────────────────────────────────────────────────────────
app.include_router(applepay_router)
app.include_router(customer_router)
app.include_router(quickbooks_router)
app.include_router(paypal_router)
app.include_router(fedex_router)