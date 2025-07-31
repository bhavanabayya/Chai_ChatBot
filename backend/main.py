import os
import sys
import io

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_openai import ChatOpenAI
from langchain.agents import Tool, AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tools.create_invoice import create_invoice_tool
from tools.summary_tool import generate_summary
from tools.tool_config import get_all_tools
from tools.quickbooks_wrapper import QuickBooksWrapper
from backend.chat_state import ChatState, ChatStage
import streamlit as st
from dotenv import load_dotenv
from pathlib import Path

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

# Initialize LangChain agent
def initialize_agent():
    tools = get_all_tools()
    llm = ChatOpenAI(
        model=OPENAI_API_MODEL or "gpt-3.5-turbo",
        temperature=0,
        openai_api_key=OPENAI_API_KEY
    )

    SYSTEM_PROMPT = """
    You are a friendly and helpful AI assistant for an e-commerce business called Chai Corner.
    Your goal is to help customers find products, add them to a cart, and complete their purchase.
    Be conversational and guide the user step-by-step.

    Here are the tools you have access to:
    {{tools}}

    Follow this process:
    1. Greet the user and ask how you can help.
    2. If the user asks about products, use products_tool.
    3. When the user wants to add a product, use the 'AddToCart' tool.
    4. Before payment, always use 'ViewCart' to confirm the order details and total with the customer.
    5. Once confirmed, use a tool from the PayPal toolkit to generate a payment link.
    6. After the user confirms they have paid, use the 'FinalizeOrder' tool to complete the process.
    7. Do not make up product IDs or prices. Only use the information provided by the tools.
    8. After the order is finalized using FinalizeOrder, use the 'create_fedex_shipment' from fedex_tool to create a shipment for the order and display the tracking number and label URL..
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
        ("human", "{input}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

    return executor

# Core interaction logic
def run_agent(query: str) -> str:
    agent_executor = initialize_agent()
    chat_state = st.session_state.chat_state
    
    if chat_state.stage == ChatStage.GREETING:
        if "order" in query.lower() or "chai" in query.lower():
            chat_state.latest_order_text = query
            chat_state.summary_text = generate_summary(query)
            chat_state.stage = ChatStage.ORDER_SUMMARY
            return f"🛍️ Here’s your order summary:\n\n{chat_state.summary_text}\n\nWould you like to proceed to generate the invoice?"

    if chat_state.stage == ChatStage.ORDER_SUMMARY and "yes" in query.lower():
        result = create_invoice_tool.invoke(f"{chat_state.latest_order_text} for customer 58")
        chat_state.stage = ChatStage.INVOICE_GENERATED
        return f"{result}\n\nShall I proceed to payment or do you want to make changes to your order?"

    if chat_state.stage == ChatStage.INVOICE_GENERATED:
        if "proceed" in query.lower() or "yes" in query.lower():
            chat_state.stage = ChatStage.AWAITING_PAYMENT_CONFIRMATION
            return "🧾 Please complete your payment using the following PayPal link:\n[Pay with PayPal](https://paypal.com/your-link)"
        elif "change" in query.lower() or "update" in query.lower():
            chat_state.stage = ChatStage.ORDER_UPDATED
            return "Sure! What changes would you like to make to your order?"

    if chat_state.stage == ChatStage.ORDER_UPDATED:
        chat_state.latest_order_text = query
        chat_state.summary_text = generate_summary(query)
        updated_invoice = create_invoice_tool.invoke(query)
        chat_state.stage = ChatStage.INVOICE_GENERATED
        return f"✅ Updated order summary:\n\n{chat_state.summary_text}\n\n{updated_invoice}\n\nWould you like to proceed to payment or make more changes?"

    return agent_executor.invoke({"input": query}).get("output", "I couldn’t understand that request.")
