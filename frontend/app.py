import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import re
import logging
from pathlib import Path
import streamlit as st

from backend.main import create_agent
# from backend.chat_state import ChatState, ChatStage

def extract_id_from_response(text: str) -> str:
    import re
    match = re.search(r"ID[:#]?\s*(\d+)", text)
    return match.group(1) if match else None


if "agent_executor" not in st.session_state:
    st.session_state.agent_executor = create_agent()

if "customer_id" not in st.session_state:
    st.session_state.customer_id = None

if "is_guest" not in st.session_state:
    st.session_state.is_guest = False

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! Welcome to Chai Corner! May I know your name to get started?"}
    ]

# if "chat_state" not in st.session_state:
#     st.session_state.chat_state = ChatState()

st.title("Chai Corner Chatbot")

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

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                agent = st.session_state.agent_executor
                response = agent.invoke({
                    "input": f"{prompt} | customer_id: {st.session_state.customer_id} | is_guest: {st.session_state.is_guest}"
                })


                # Extract customer_id from the agent response (if it exists)
                if "ID:" in response:
                    new_id = extract_id_from_response(response)
                    if new_id:
                        st.session_state.customer_id = new_id


                agent_response = response.get("output", "Sorry, I ran into an issue.")
                if "customer_id" in response:
                    st.session_state.customer_id = response["customer_id"]
                    print(f"✅ Stored customer_id: {st.session_state.customer_id}")
                st.markdown(agent_response)
                # Add agent's response to chat history
                st.session_state.messages.append({"role": "assistant", "content": agent_response})

                #  Show download button if invoice is generated
                if "Download Invoice" in agent_response:
                    match = re.search(r"/download/(invoice_\d+\.pdf)", agent_response)
                    if match:
                        DOWNLOAD_DIR = Path(__file__).parent.parent / "invoices"
                        pdf_path = DOWNLOAD_DIR / match.group(1)
                        if pdf_path.exists():
                            with open(pdf_path, "rb") as f:
                                st.download_button(
                                    label=" Download Invoice PDF",
                                    data=f,
                                    file_name=match.group(1),
                                    mime="application/pdf"
                                )
                                
            except Exception as e:
                error_message = f"An error occurred: {e}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

            # st.markdown(agent_response)


    # Save assistant message to session
    # st.session_state.messages.append({"role": "assistant", "content": agent_response})
