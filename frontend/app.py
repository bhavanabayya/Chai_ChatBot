import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import re
import logging
from pathlib import Path
import streamlit as st

from backend.main import create_agent
from backend.chat_state import get_state, set_customer  # ✅ use centralized state

def extract_id_from_response(text: str) -> str:
    import re
    match = re.search(r"ID[:#]?\s*(\d+)", text)
    return match.group(1) if match else None

if "agent_executor" not in st.session_state:
    st.session_state.agent_executor = create_agent()

# ✅ NO separate customer_id / is_guest keys anymore

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! Welcome to Chai Corner! May I know your name to get started?"}
    ]

st.title("Chai Corner Chatbot")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What can I help you with today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                agent = st.session_state.agent_executor
                state = get_state()  # ✅ centralized
                response = agent.invoke({
                    "input": f"{prompt} | customer_id: {state.customer_id} | is_guest: {state.is_guest}"
                })

                # Fallback: try to capture a raw ID pattern
                raw_text = response if isinstance(response, str) else response.get("output", "")
                new_id = extract_id_from_response(raw_text)
                if new_id:
                    set_customer(new_id)  # ✅ centralized

                agent_response = response.get("output", "Sorry, I ran into an issue.")
                st.markdown(agent_response)
                st.session_state.messages.append({"role": "assistant", "content": agent_response})

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
