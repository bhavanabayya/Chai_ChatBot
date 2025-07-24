import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory

from tools.tool_config import get_all_tools
from backend.chat_state import ChatState, ChatStage

load_dotenv()

# Load tools
intuit_tool, venmo_tool, fedex_tool, calendar_tool, gmail_tool = get_all_tools()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": " Hi! Welcome to Chai Corner! How can I help you today?"}
    ]

if "chat_state" not in st.session_state:
    st.session_state.chat_state = ChatState()

st.title(" Chai Corner Chatbot")
prompt = st.chat_input("Type your message:")

# Display chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt:
    # Show user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Chatbot logic
    response = ""
    session = st.session_state.chat_state

    if session.stage == ChatStage.GREETING:
        if any(word in prompt.lower() for word in ["order", "chai", "coffee"]):
            order = prompt
            invoice_url = intuit_tool(order)  # should return just the URL string
            session.order = order
            session.invoice_link = invoice_url
            session.stage = ChatStage.INVOICE_SENT

            response = (
                f" Sure! Here's your invoice for the order: [View Invoice]({invoice_url})\n\n"
                "Would you like to add items, change the order, or proceed to payment?"
            )
        else:
            response = " I'm here to help with chai orders, invoices, payments, and shipping!"

    elif session.stage == ChatStage.INVOICE_SENT:
        if "proceed" in prompt.lower():
            session.stage = ChatStage.PAYMENT_LINK_SENT
            response = f"💳 Please proceed with the payment using this Venmo link: [{session.venmo_link}]({session.venmo_link})"
        elif "change" in prompt.lower() or "add" in prompt.lower():
            updated_order = prompt
            session.order = updated_order
            session.invoice_link = intuit_tool(updated_order)
            response = f"🔄 Your order has been updated. Here is your new invoice: [View Invoice]({session.invoice_link})\n\nWould you like to proceed to payment?"
        else:
            response = " Please type 'proceed' or 'change' to continue."

    elif session.stage == ChatStage.PAYMENT_LINK_SENT:
        if "paid" in prompt.lower():
            label_link = fedex_tool(session.order)
            session.shipping_label = label_link
            session.stage = ChatStage.SHIPPING_LABEL_SENT
            response = f" Payment confirmed!  Here is your shipping label: [Track Shipment]({label_link})\n\nThank you for your order!"
        else:
            response = " Once you've paid, let me know by typing 'I have paid'."

    elif session.stage == ChatStage.SHIPPING_LABEL_SENT:
        response = " Your chai is on its way! Anything else I can help you with?"

    else:
        response = " I didn't quite catch that. Could you rephrase?"

    st.chat_message("assistant").markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
