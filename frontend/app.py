import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st

from backend.main import create_agent
# from backend.chat_state import ChatState, ChatStage

if "agent_executor" not in st.session_state:
    st.session_state.agent_executor = create_agent()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! Welcome to Chai Corner! How can I help you today?"}
    ]

# if "chat_state" not in st.session_state:
#     st.session_state.chat_state = ChatState()

st.title("Chai Corner Chatbot")
# prompt = st.chat_input("Type your message:")

# --- Display Chat Messages ---
# Iterate through the messages stored in session_state and display them.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Handle User Input ---
if prompt := st.chat_input("What can I help you with today?"):
    # Add and display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get agent's response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                agent = st.session_state.agent_executor
                response = agent.invoke({"input": prompt})
                agent_response = response.get("output", "Sorry, I ran into an issue.")
                
                st.markdown(agent_response)
                # Add agent's response to chat history
                st.session_state.messages.append({"role": "assistant", "content": agent_response})
            
            except Exception as e:
                error_message = f"An error occurred: {e}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
