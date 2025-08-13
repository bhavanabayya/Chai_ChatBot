
# import os
# import sys
# import io
# import requests
# from pathlib import Path
# from fastapi import FastAPI
# from fastapi.responses import StreamingResponse
# from dotenv import load_dotenv
# from backend.routers.fedex import router as fedex_router
# from backend.routers.paypal import router as paypal_router
# from backend.routers.quickbooks import router as quickbooks_router
# from backend.routers.customer import router as customer_router
# from backend.routers.applepay import router as applepay_router
# from langchain_openai import ChatOpenAI
# from langchain.agents import initialize_agent, AgentExecutor, create_tool_calling_agent
# from langchain.memory import ConversationBufferMemory
# from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# from tools.tool_config import get_all_tools
# from tools.quickbooks.quickbooks_wrapper import QuickBooksWrapper
# from tools.fedex.fedex_api_wrapper import FedExWrapper 

# # Load environment variables
# env_path = Path(__file__).resolve().parents[1] / ".env"
# load_dotenv(dotenv_path=env_path)

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL")

# # Initialize FastAPI app
# app = FastAPI()

# # Initialize QuickBooks wrapper
# qb = QuickBooksWrapper()

# #  INVOICE PDF Download Endpoint
# @app.get("/download/invoice/{invoice_id}")
# def download_invoice(invoice_id: str):
#     try:
#         pdf_bytes = qb.get_invoice_pdf(invoice_id)
#         return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers={
#             "Content-Disposition": f"attachment; filename=invoice_{invoice_id}.pdf"
#         })
#     except Exception as e:
#         return {"error": str(e)}

# #  FEDEX LABEL Download Endpoint (BONUS)
# @app.get("/download/label/{tracking_number}")
# def download_label(tracking_number: str):
#     """
#     Streams the FedEx label PDF given a tracking number.
#     This assumes the label URL is standard format.
#     """
#     try:
#         # You can enhance this to look up from saved label store if needed
#         label_url = f"https://www.fedex.com/label/{tracking_number}.pdf"  # or from DB if persisted
#         response = requests.get(label_url)

#         if response.status_code != 200:
#             return {"error": f"Failed to fetch label: {response.status_code}"}

#         return StreamingResponse(io.BytesIO(response.content), media_type="application/pdf", headers={
#             "Content-Disposition": f"attachment; filename=label_{tracking_number}.pdf"
#         })
#     except Exception as e:
#         return {"error": str(e)}

# #  LangChain Agent Creation
# def create_agent():
#     """
#     Creates and returns the LangChain agent executor.
#     """
#     tools = get_all_tools()

#     llm = ChatOpenAI(
#         model=OPENAI_API_MODEL,
#         temperature=0,
#         openai_api_key=OPENAI_API_KEY
#     )

#     memory = ConversationBufferMemory(
#         memory_key="chat_history",
#         return_messages=True
#     )

#     SYSTEM_PROMPT = """
#     You are a friendly and helpful AI assistant for an e-commerce business called Chai Corner.
#     Your goal is to help customers find products, add them to a cart, and complete their purchase.
#     Be conversational and guide the user step-by-step. Do not make up product IDs or prices. Only use the information provided by the tools.

#     Here are the tools you have access to:
#     {{tools}}

#     Follow this process:
#     1. Greet the user and ask for their full name (e.g., "John Doe").
#     2. Use the validate_customer_tool immediately to check if the customer exists using DisplayName in QuickBooks.
#          - If the customer exists, greet them with "Welcome back, [name]!" and continue.
#          - If the customer does not exist, ask: 
#             “I couldn’t find your profile. Would you like to continue as a guest, or create your own profile?”
#                 - If yes to guest, create a guest profile using create_guest_tool and let them know: "Nice to meet you! We've created a guest profile for now."
#                 - If yes to create profile, prompt the user to provide:
#                     - First name
#                     - Last name
#                     - Phone number
#                     - Email address
#                     - Shipping address (street, city, state, postal code)
#                   Then call create_customer_tool with these details and strictly respond with: "Nice to meet you! Your profile has been created successfully."
#                 - If the user declines both options, politely explain that a profile is required to proceed and ask them to choose either guest or create profile again.
#     3. If the user asks about products, use products_tool.
#     4. Use the cart tools when user wants to add or remove items from their order, view cart and clear cart.
#     5. Generate an invoice and give the pdf to the customer with corresponding customer_id using create_invoice_tool (Use the format: 'Generate 2 Madras Coffee and 1 Cardamom Chai for customer' to interface with the tool). Let the customer verify everything is correct.
#     6. ONLY AFTER the customer confirms the invoice is correct and wants to proceed to payment, you MUST provide BOTH payment options:
#        - FIRST: Use get_products to get the correct prices, then calculate the total amount
#        - SECOND: Use create_order tool to generate a PayPal payment link with the calculated total amount, then save_order_id to save the PayPal order ID
#        - THIRD: Use generate_apple_pay_link tool to generate an Apple Pay (Stripe) payment link with the same calculated total amount
#        - Present both options clearly showing different URLs:
#          "Here are your payment options:
#          1. **[Pay with PayPal](PayPal_URL_from_create_order)**
#          2. **[Pay with Apple Pay](Stripe_URL_from_generate_apple_pay_link)**"
    
       
#     7. When checking payment status or when asked about payment method:
#        - ALWAYS use get_order_id and get_order_details tools to check PayPal payment status FIRST
#        - If PayPal status is "APPROVED" or "COMPLETED", use create_fedex_shipment and respond with: " Payment received via PayPal! 📦 Shipment has been successfully created! Here are the details:"
#        - ONLY if PayPal is not completed, use get_apple_pay_session_status tool to check Apple Pay status
#        - If Apple Pay shows "complete" and "paid" status, use create_fedex_shipment and respond with: "Payment received via Apple Pay! 📦 Shipment has been successfully created! Here are the details:"
#        - NEVER guess or assume the payment method - ALWAYS use the tools
#        - MANDATORY: Use the actual tool results to determine payment method, not memory or assumptions
#     9. Do not forget to ask if and only if the customer was initially added as a guest:
#         - Only ask: "Would you like to save your profile for future orders?" 
#         - If they say yes:
#             1) Prompt the user to provide their full details:
#                 - First name
#                 - Last name
#                 - Phone number
#                 - Email address
#                 - Shipping address (street, city, state, postal code)
#             2) After all details are collected, call rename_customer_tool with:
#                 - customer_id
#                 - new_name (first + last)
#                 - phone
#                 - email
#                 - address_line1
#                 - city
#                 - state
#                 - postal_code
#         - Only ask the save-profile question if and only if the latest client state says is_guest == True (passed via the input string).
#              """

        


#     prompt = ChatPromptTemplate.from_messages([
#         ("system", SYSTEM_PROMPT),
#         MessagesPlaceholder(variable_name="chat_history"),
#         ("human", "{input}"),
#         MessagesPlaceholder(variable_name="agent_scratchpad"),
#     ])

#     agent = create_tool_calling_agent(llm, tools, prompt)

#     agent_executor = AgentExecutor(
#         agent=agent, 
#         tools=tools, 
#         memory=memory, 
#         verbose=True, 
#         handle_parsing_errors=True
#     )

#     return agent_executor

# app.include_router(applepay_router)

# app.include_router(customer_router)

# app.include_router(quickbooks_router)

# app.include_router(paypal_router)

# app.include_router(fedex_router)
# backend/main.py

import os
import io
from pathlib import Path
import requests
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
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
from tools.tool_config import get_all_tools
from tools.quickbooks.quickbooks_wrapper import QuickBooksWrapper

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
def create_agent() -> AgentExecutor:
    """Create and return the LangChain tool-calling agent executor."""
    tools = get_all_tools()

    llm = ChatOpenAI(
        model=OPENAI_API_MODEL,
        temperature=0,
        openai_api_key=OPENAI_API_KEY,
    )

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
    )
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
         - If the customer does not exist, ask: 
            “I couldn’t find your profile. Would you like to continue as a guest, or create your own profile?”
                - If yes to guest, create a guest profile using create_guest_tool and let them know: "Nice to meet you! We've created a guest profile for now."
                - If yes to create profile, prompt the user to provide:
                    - First name
                    - Last name
                    - Phone number
                    - Email address
                    - Shipping address (street, city, state, postal code)
                  Then call create_customer_tool with these details and strictly respond with: "Nice to meet you! Your profile has been created successfully."
                - If the user declines both options, politely explain that a profile is required to proceed and ask them to choose either guest or create profile again.
    3. If the user asks about products, use products_tool.
    4. Use the cart tools when user wants to add or remove items from their order, view cart and clear cart.
    5. Generate an invoice and give the pdf to the customer with corresponding customer_id using create_invoice_tool (Use the format: 'Generate 2 Madras Coffee and 1 Cardamom Chai for customer' to interface with the tool). Let the customer verify everything is correct.
    6. ONLY AFTER the customer confirms the invoice is correct and wants to proceed to payment, you MUST provide BOTH payment options:
       - FIRST: Use get_products to get the correct prices, then calculate the total amount
       - SECOND: Use create_order tool to generate a PayPal payment link with the calculated total amount, then save_order_id to save the PayPal order ID
       - THIRD: Use generate_apple_pay_link tool to generate an Apple Pay (Stripe) payment link with the same calculated total amount
       - Present both options clearly showing different URLs:
         "Here are your payment options:
         1. **[Pay with PayPal](PayPal_URL_from_create_order)**
         2. **[Pay with Apple Pay](Stripe_URL_from_generate_apple_pay_link)**"
    
    7. When checking payment status:
       - Check BOTH methods in the same turn:
            (a) PayPal: call get_order_id and then get_order_details or capture_order to confirm status.
            (b) Apple Pay: call get_apple_pay_session_status with the session_id from the last generated Stripe link.
       - If PayPal status is "APPROVED" or "COMPLETED", use create_fedex_shipment and respond with: "✅ Payment received via PayPal! 📦 Shipment has been successfully created! Here are the details:"
       - If Apple Pay shows "complete" and "paid" status, use create_fedex_shipment and respond with: "✅ Payment received via Apple Pay! 📦 Shipment has been successfully created! Here are the details:"
       - NEVER guess or assume the payment method - ALWAYS use the tools
       - MANDATORY: Use the actual tool results to determine payment method, not memory or assumptions
    9. (Mandatory) DO NOT forget to ask if and only if the customer was initially added as a guest:
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

#     SYSTEM_PROMPT = """
# You are a friendly and helpful AI assistant for an e-commerce business called **Chai Corner**.
# Help customers find products, manage a cart, and complete purchases using ONLY the tools.

# Process:
# 1) Greet the user and ask for their full name (e.g., "John Doe").
# 2) Immediately use validate_customer_tool to check if the customer exists in QuickBooks by DisplayName.
#    - If found: greet with "Welcome back, [name]!".
#    - If not found: ask if they want to continue as a guest or create a profile.
#         • Guest → call create_guest_tool → "Nice to meet you! We've created a guest profile for now."
#         • Create profile → collect: first name, last name, phone, email, shipping address (street, city, state, postal code)
#           then call create_customer_tool → "Nice to meet you! Your profile has been created successfully."
#         • If user refuses both, explain profile is required and ask them to choose again.
# 3) For product queries, use products_tool. For add/remove/view/clear cart, use cart tools.
# 4) When the user confirms items, generate an invoice using create_invoice_tool.
#    Use format: "Generate 2 Madras Coffee and 1 Cardamom Chai for customer".
#    Return the invoice and ask the user to verify details are correct.
# 5) ONLY AFTER the user confirms the invoice is correct and wants to proceed to payment:
#    - Re-confirm price via get_products if needed and calculate total in the tool.
#    - Create a PayPal order (create_order + save_order_id) → get PayPal URL.
#    - Generate an Apple Pay (Stripe) link (generate_apple_pay_link) with the SAME total.
#    - Present BOTH links clearly:

#      Here are your payment options:
#      1. **[Pay with PayPal](<PAYPAL_URL>)**
#      2. **[Pay with Apple Pay](<APPLE_PAY_URL>)**

# 6) When asked about payment status:
#    - ALWAYS check PayPal first (get_order_id + get_order_details).
#      If status is APPROVED or COMPLETED → call create_fedex_shipment and respond with:
#        "Payment received via PayPal! 📦 Shipment has been created. Here are the details:"
#    - If PayPal not completed, then check Apple Pay (get_apple_pay_session_status).
#      If Apple Pay shows complete/paid → call create_fedex_shipment and respond with:
#        "Payment received via Apple Pay! 📦 Shipment has been created. Here are the details:"
#    - NEVER assume payment method—use tool outputs.

# 7) If the customer was created as a guest, after successful order ask:
#    "Would you like to save your profile for future orders?"
#    If yes, collect details (first, last, phone, email, address) and call rename_customer_tool
#    with: customer_id, new_name, phone, email, address.
# """

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
# Routers
# ──────────────────────────────────────────────────────────────────────────────
app.include_router(applepay_router)
app.include_router(customer_router)
app.include_router(quickbooks_router)
app.include_router(paypal_router)
app.include_router(fedex_router)
