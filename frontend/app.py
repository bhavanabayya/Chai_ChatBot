import sys
import os
import re
import logging
from pathlib import Path
import streamlit as st

# Setup paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.main import run_agent
from backend.chat_state import ChatState

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("chatbot_debug.log"),
        logging.StreamHandler()
    ]
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! Welcome to Chai Corner! How can I help you today?"}
    ]

if "chat_state" not in st.session_state:
    st.session_state.chat_state = ChatState()

st.title("Chai Corner Chatbot")

# --- Display Chat Messages ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Handle User Input ---
if prompt := st.chat_input("What can I help you with today?"):
    # Log user input
    logging.info(f" User: {prompt}")

    # Add user message to session
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                agent_response = run_agent(prompt)
                logging.info(" Agent response generated.")
            except Exception as e:
                agent_response = f" An error occurred: {str(e)}"
                logging.error(f"Exception during agent execution: {str(e)}")

            st.markdown(agent_response)

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

    # Save assistant message to session
    st.session_state.messages.append({"role": "assistant", "content": agent_response})
