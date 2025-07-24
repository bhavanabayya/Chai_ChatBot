
import os
from dotenv import load_dotenv
import streamlit as st

from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory

from tools.tool_config import get_all_tools
from backend.chat_state import ChatState, ChatStage

# Load .env
load_dotenv()

# Initialize session state
if "session" not in st.session_state:
    st.session_state.session = ChatState()

# Initialize LLM
llm = ChatOpenAI(
    temperature=0,
    model="gpt-4",  
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# Memory and tools
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
tools = get_all_tools()

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    memory=memory,
    verbose=True
)

# Streamlit UI
st.set_page_config(page_title="Chai Corner Chatbot")
st.title("Chai Corner Chatbot")

user_input = st.text_input("Say something:", key="user_input")

if user_input:
    session = st.session_state.session

    if session.stage == ChatStage.GREETING:
        session.stage = ChatStage.ORDER_TAKING
        st.markdown(" Hi! Welcome to Chai Corner! How can I help you today?")

    elif session.stage == ChatStage.ORDER_TAKING:
        session.order_details = user_input
        result = agent.invoke({"input": f"Generate invoice for: {user_input}"})
        session.invoice_link = result if isinstance(result, str) else str(result)
        session.stage = ChatStage.AFTER_INVOICE
        st.markdown(f" Invoice generated: {session.invoice_link}")
        st.markdown("Would you like to add/change items or proceed to payment?")

    elif session.stage == ChatStage.AFTER_INVOICE:
        if "proceed" in user_input.lower():
            session.stage = ChatStage.PAYMENT
            st.markdown(f" You can pay using Venmo: {session.venmo_link}")
        elif "add" in user_input.lower() or "change" in user_input.lower():
            session.stage = ChatStage.UPDATED_ORDER
            st.markdown(" What changes would you like to make to your order?")
        else:
            st.warning("Please say if you'd like to update the order or proceed to payment.")

    elif session.stage == ChatStage.UPDATED_ORDER:
        session.updated_order = user_input
        result = agent.invoke({"input": f"Generate updated invoice for: {user_input}"})
        session.invoice_link = result if isinstance(result, str) else str(result)
        session.stage = ChatStage.AFTER_INVOICE
        st.markdown(f" Updated invoice: {session.invoice_link}")
        st.markdown("Would you like to proceed to payment?")

    elif session.stage == ChatStage.PAYMENT:
        session.stage = ChatStage.SHIPPING
        result = agent.invoke({"input": f"Generate FedEx shipping label for: {session.order_details}"})
        session.shipping_label = result if isinstance(result, str) else str(result)
        st.markdown(f" Payment confirmed. Shipping label: {session.shipping_label}")

    else:
        st.warning("Something went wrong. Please say 'hi' to restart.")
