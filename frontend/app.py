import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import re
import logging
import time
from pathlib import Path
import streamlit as st

from backend.main import create_agent
# from backend.chat_state import ChatState, ChatStage

def extract_id_from_response(text: str) -> str:
    import re
    match = re.search(r"ID[:#]?\s*(\d+)", text)
    return match.group(1) if match else None

def extract_payment_ids(text: str):
    """Extract PayPal order ID and Apple Pay session ID from agent response"""
    paypal_id = None
    apple_pay_id = None
    
    # Extract PayPal order ID from the URL
    paypal_match = re.search(r'paypal\.com/checkoutnow\?token=([A-Z0-9]+)', text)
    if paypal_match:
        paypal_id = paypal_match.group(1)
    
    # Extract Apple Pay session ID from the URL
    apple_pay_match = re.search(r'checkout\.stripe\.com/c/pay/(cs_test_[A-Za-z0-9]+)', text)
    if apple_pay_match:
        apple_pay_id = apple_pay_match.group(1)
    
    return paypal_id, apple_pay_id


if "agent_executor" not in st.session_state:
    st.session_state.agent_executor = create_agent()

if "customer_id" not in st.session_state:
    st.session_state.customer_id = None

if "is_guest" not in st.session_state:
    st.session_state.is_guest = False

# Payment monitoring variables
if "payment_polling" not in st.session_state:
    st.session_state.payment_polling = False

if "last_payment_check" not in st.session_state:
    st.session_state.last_payment_check = 0

if "paypal_order_id" not in st.session_state:
    st.session_state.paypal_order_id = None

if "apple_pay_session_id" not in st.session_state:
    st.session_state.apple_pay_session_id = None

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
                
                # Start payment monitoring if payment links are detected
                if "Pay with PayPal" in agent_response and "Pay with Apple Pay" in agent_response:
                    # Extract and save payment IDs
                    paypal_id, apple_pay_id = extract_payment_ids(agent_response)
                    st.session_state.paypal_order_id = paypal_id
                    st.session_state.apple_pay_session_id = apple_pay_id

                    st.session_state.payment_polling = True
                    st.session_state.last_payment_check = time.time()
                    print(f"🔄 Started payment monitoring - PayPal: {paypal_id}, Apple Pay: {apple_pay_id}")
                
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


# --- Payment Status Monitoring ---
# Check payment status automatically when polling is active
if st.session_state.payment_polling:
    current_time = time.time()
    if current_time - st.session_state.last_payment_check >= 10:  # Check every 10 seconds (less frequent)
        st.session_state.last_payment_check = current_time
        
        try:
            # Check payment status silently - only respond when truly completed
            agent = st.session_state.agent_executor
            paypal_id = st.session_state.paypal_order_id
            apple_pay_id = st.session_state.apple_pay_session_id

            # Use a more specific input that only checks for completed payments
            check_input = f"Silently check if payment is completed for paypal_order_id: {paypal_id} or apple_pay_session_id: {apple_pay_id}. Only respond if payment is FULLY COMPLETED and PAID, otherwise say 'still waiting'"

            response = agent.invoke({
                "input": check_input
            })

            payment_response = response.get("output", "")

            # Only respond if payment is truly completed (not just initiated or pending)
            if any(keyword in payment_response.lower() for keyword in
                   ["payment received via paypal", "payment received via apple pay", "order has been confirmed", "shipment has been successfully created", "tracking number", "successfully processed", "payment successful"]) and "still waiting" not in payment_response.lower():
                # Payment successful - stop polling and show message
                st.session_state.payment_polling = False
                with st.chat_message("assistant"):
                    st.markdown(payment_response)
                st.session_state.messages.append({"role": "assistant", "content": payment_response})
                st.rerun()

        except Exception as e:
            print(f"Payment monitoring error: {e}")
    
    # Auto-refresh every 5 seconds when monitoring (less frequent)
    time.sleep(5)
    st.rerun()

# --- Payment Status Indicator ---
if st.session_state.payment_polling:
    st.sidebar.markdown("🔄 **Monitoring Payment Status...**")
    st.sidebar.markdown("The system is automatically checking for payment completion.")
    if st.sidebar.button("Stop Monitoring"):
        st.session_state.payment_polling = False
        st.rerun()
