import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st

from backend.main import run_agent
from backend.chat_state import ChatState, ChatStage


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! Welcome to Chai Corner! How can I help you today?"}
    ]

if "chat_state" not in st.session_state:
    st.session_state.chat_state = ChatState()

st.title("Chai Corner Chatbot")
# prompt = st.chat_input("Type your message:")

# --- Initialize Chat History in Session State ---
# This ensures that the chat history persists across reruns of the app.
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Display Chat Messages ---
# Iterate through the messages stored in session_state and display them.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Handle User Input ---
# Create a chat input box for the user to type their queries.
if prompt := st.chat_input("What can I help you with today?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat UI
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get agent's response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Call the run_agent function from agent.py
            agent_response = run_agent(prompt)
            st.markdown(agent_response)
    
    # Add agent's response to chat history
    st.session_state.messages.append({"role": "assistant", "content": agent_response})
