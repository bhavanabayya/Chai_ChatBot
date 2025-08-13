# # frontend/app.py

# import os
# import sys
# import io
# import time
# import re
# import logging
# from pathlib import Path

# import streamlit as st

# # Ensure backend package import works when running from /frontend
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# from backend.utils import extract_id_from_response
# from backend.main import create_agent
# from backend.chat_state import get_state, set_customer

# # ──────────────────────────────────────────────────────────────────────────────
# # Helpers
# # ──────────────────────────────────────────────────────────────────────────────
# def extract_payment_ids(text: str):
#     """Extract PayPal order ID and Apple Pay session ID from assistant response."""
#     paypal_id = None
#     apple_pay_id = None

#     # PayPal order token (e.g., https://www.paypal.com/checkoutnow?token=XXXX)
#     m = re.search(r'paypal\.com/checkoutnow\?token=([A-Z0-9-]+)', text)
#     if m:
#         paypal_id = m.group(1)

#     # Stripe checkout session id (e.g., https://checkout.stripe.com/c/pay/cs_test_...)
#     m = re.search(r'checkout\.stripe\.com/c/pay/(cs_test_[A-Za-z0-9_]+)', text)
#     if m:
#         apple_pay_id = m.group(1)

#     return paypal_id, apple_pay_id


# def render_payment_links(paypal_id: str | None, apple_pay_id: str | None):
#     """Render both links (if present) in a consistent way."""
#     lines = []
#     if paypal_id:
#         paypal_url = f"https://www.paypal.com/checkoutnow?token={paypal_id}"
#         lines.append(f"1. **[Pay with PayPal]({paypal_url})**")
#     if apple_pay_id:
#         apple_url = f"https://checkout.stripe.com/c/pay/{apple_pay_id}"
#         lines.append(f"2. **[Pay with Apple Pay]({apple_url})**")
#     if lines:
#         st.markdown("Here are your payment options:\n\n" + "\n\n".join(lines))


# # ──────────────────────────────────────────────────────────────────────────────
# # Session State Init
# # ──────────────────────────────────────────────────────────────────────────────
# if "agent_executor" not in st.session_state:
#     st.session_state.agent_executor = create_agent()

# if "customer_id" not in st.session_state:
#     st.session_state.customer_id = None
# if "payment_prompted" not in st.session_state:
#     st.session_state.payment_prompted = False

# if "is_guest" not in st.session_state:
#     st.session_state.is_guest = False

# if "messages" not in st.session_state:
#     st.session_state.messages = [
#         {"role": "assistant", "content": "Hi! Welcome to Chai Corner! May I know your name to get started?"}
#     ]

# # Payment monitoring state
# if "payment_polling" not in st.session_state:
#     st.session_state.payment_polling = False
# if "last_payment_check" not in st.session_state:
#     st.session_state.last_payment_check = 0.0
# if "paypal_order_id" not in st.session_state:
#     st.session_state.paypal_order_id = None
# if "apple_pay_session_id" not in st.session_state:
#     st.session_state.apple_pay_session_id = None

# # ──────────────────────────────────────────────────────────────────────────────
# # UI
# # ──────────────────────────────────────────────────────────────────────────────
# st.title("Chai Corner Chatbot")

# # Display chat history
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])

# # ──────────────────────────────────────────────────────────────────────────────
# # Handle user input
# # ──────────────────────────────────────────────────────────────────────────────
# if prompt := st.chat_input("What can I help you with today?"):
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     with st.chat_message("assistant"):
#         with st.spinner("Thinking..."):
#             try:
#                 agent = st.session_state.agent_executor
#                 state = get_state()  # pulls latest (customer_id, is_guest) from backend state

#                 # Include state in the prompt so tools can use it deterministically
#                 agent_input = f"{prompt} | customer_id: {state.customer_id} | is_guest: {state.is_guest}"
#                 response = agent.invoke({"input": agent_input})

#                 # Agent output text
#                 agent_response = response.get("output", "Sorry, I ran into an issue.")

#                 # Try to capture a raw ID pattern as fallback and update backend state if found
#                 new_id = extract_id_from_response(agent_response)
#                 if new_id:
#                     set_customer(new_id)

#                 # Also accept explicit customer_id in response payload (if a tool returned it)
#                 if isinstance(response, dict) and "customer_id" in response and response["customer_id"]:
#                     st.session_state.customer_id = response["customer_id"]

#                 # Detect payment links and set polling if present
#                 paypal_id, apple_pay_id = extract_payment_ids(agent_response)
#                 if paypal_id or apple_pay_id:
#                     st.session_state.paypal_order_id = paypal_id
#                     st.session_state.apple_pay_session_id = apple_pay_id
#                     st.session_state.payment_polling = True
#                     st.session_state.last_payment_check = time.time()

#                 # Render assistant message
#                 st.markdown(agent_response)
#                 # Render payment options clearly beneath any assistant text
#                 render_payment_links(paypal_id, apple_pay_id)

#                 # Persist assistant message in history
#                 st.session_state.messages.append({"role": "assistant", "content": agent_response})

#                 # Optional: In-app invoice download if you’re saving PDFs locally (disabled by default)
#                 # if "Download Invoice" in agent_response:
#                 #     match = re.search(r"/download/(invoice_\d+\.pdf)", agent_response)
#                 #     if match:
#                 #         download_dir = Path(__file__).parent.parent / "invoices"
#                 #         pdf_path = download_dir / match.group(1)
#                 #         if pdf_path.exists():
#                 #             with open(pdf_path, "rb") as f:
#                 #                 st.download_button(
#                 #                     label=" Download Invoice PDF",
#                 #                     data=f,
#                 #                     file_name=match.group(1),
#                 #                     mime="application/pdf",
#                 #                 )

#             except Exception as e:
#                 error_message = f"An error occurred: {e}"
#                 st.error(error_message)
#                 st.session_state.messages.append({"role": "assistant", "content": error_message})

# # ──────────────────────────────────────────────────────────────────────────────
# # Background payment status monitoring (lightweight)
# # ──────────────────────────────────────────────────────────────────────────────
# if st.session_state.payment_polling:
#     current_time = time.time()
#     # Check every 12 seconds to be gentle on APIs and UI
#     if current_time - st.session_state.last_payment_check >= 12:
#         st.session_state.last_payment_check = current_time
#         try:
#             agent = st.session_state.agent_executor
#             paypal_id = st.session_state.paypal_order_id
#             apple_pay_id = st.session_state.apple_pay_session_id

#             # Be explicit: only announce when payment is confirmed/complete
#             check_input = (
#                 "Silently check if payment is completed for "
#                 f"paypal_order_id: {paypal_id} or apple_pay_session_id: {apple_pay_id}. "
#                 "Only respond if payment is FULLY COMPLETED and PAID with shipment created; "
#                 "otherwise respond exactly 'still waiting'."
#             )
#             check_resp = agent.invoke({"input": check_input})
#             payment_response = check_resp.get("output", "")

#             # If payment is fully done, post message and stop polling
#             if payment_response and payment_response.lower() != "still waiting":
#                 st.session_state.payment_polling = False
#                 with st.chat_message("assistant"):
#                     st.markdown(payment_response)
#                 st.session_state.messages.append({"role": "assistant", "content": payment_response})
#                 st.rerun()

#         except Exception as e:
#             logging.warning(f"Payment monitoring error: {e}")

#     # Subtle auto-refresh while monitoring
#     time.sleep(5)
#     st.rerun()

# # ──────────────────────────────────────────────────────────────────────────────
# # Sidebar indicator/controls for monitoring
# # ──────────────────────────────────────────────────────────────────────────────
# if st.session_state.payment_polling:
#     st.sidebar.markdown("🔄 **Monitoring Payment Status…**")
#     st.sidebar.markdown("I'll update you once payment is confirmed and the shipment is created.")
#     if st.sidebar.button("Stop Monitoring"):
#         st.session_state.payment_polling = False
#         st.rerun()
# frontend/app.py

import os
import sys
import io
import time
import re
import logging
from pathlib import Path

import streamlit as st

# Ensure backend package import works when running from /frontend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.utils import extract_id_from_response
from backend.main import create_agent
from backend.chat_state import get_state, set_customer

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def strip_existing_payment_block(text: str) -> str:
    """Remove any 'Here are your payment options' section from LLM output to avoid duplicates."""
    return re.sub(
        r"Here are your payment options:[\s\S]*$",
        "",
        text,
        flags=re.IGNORECASE
    ).strip()

def extract_payment_urls(text: str):
    """
    Prefer full URLs returned by tools.
    Fallbacks:
      - PayPal: if only token present, build a *sandbox* URL.
      - Stripe: avoid rebuilding; try to capture full checkout.stripe.com URL.
    Returns (paypal_url, apple_url, paypal_token, stripe_session_id)
    """
    paypal_url = None
    apple_url = None
    paypal_token = None
    stripe_session_id = None

    # FULL PayPal approve URL (sandbox or live)
    m = re.search(r'(https?://(?:www\.|sandbox\.)?paypal\.com/checkoutnow\?token=[A-Za-z0-9\-._]+)', text)
    if m:
        paypal_url = m.group(1)

    # FULL Stripe Checkout URL
    m = re.search(r'(https?://checkout\.stripe\.com/[^\s)]+)', text)
    if m:
        apple_url = m.group(1)

    # Fallbacks if only fragments exist
    if not paypal_url:
        m = re.search(r'paypal\.com/checkoutnow\?token=([A-Z0-9\-._]+)', text)
        if m:
            paypal_token = m.group(1)
            # Use sandbox domain in dev/sandbox
            paypal_url = f"https://www.sandbox.paypal.com/checkoutnow?token={paypal_token}"

    if not apple_url:
        m = re.search(r'checkout\.stripe\.com/(?:c/pay|pay)/([A-Za-z0-9_\-]+)', text)
        if m:
            stripe_session_id = m.group(1)
            # Do not attempt to reconstruct; rely on full url from tool when possible.

    return paypal_url, apple_url, paypal_token, stripe_session_id


def build_payment_block(paypal_url: str | None, apple_url: str | None) -> str:
    """Return a canonical payment options markdown block (or empty string)."""
    lines = []
    if paypal_url:
        lines.append(f"1. **[Pay with PayPal]({paypal_url})**")
    if apple_url:
        lines.append(f"2. **[Pay with Apple Pay]({apple_url})**")
    if not lines:
        return ""
    return "Here are your payment options:\n\n" + "\n\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# Session State Init
# ──────────────────────────────────────────────────────────────────────────────
if "agent_executor" not in st.session_state:
    st.session_state.agent_executor = create_agent()

if "customer_id" not in st.session_state:
    st.session_state.customer_id = None

if "is_guest" not in st.session_state:
    st.session_state.is_guest = False

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! Welcome to Chai Corner! May I know your name to get started?"}
    ]

# Payment url + monitoring state
if "paypal_url" not in st.session_state:
    st.session_state.paypal_url = None
if "apple_pay_url" not in st.session_state:
    st.session_state.apple_pay_url = None
if "paypal_order_id" not in st.session_state:
    st.session_state.paypal_order_id = None
if "apple_pay_session_id" not in st.session_state:
    st.session_state.apple_pay_session_id = None
if "payment_polling" not in st.session_state:
    st.session_state.payment_polling = False
if "last_payment_check" not in st.session_state:
    st.session_state.last_payment_check = 0.0

# ──────────────────────────────────────────────────────────────────────────────
# UI
# ──────────────────────────────────────────────────────────────────────────────
st.title("Chai Corner Chatbot")

# Display chat history (single source of truth)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ──────────────────────────────────────────────────────────────────────────────
# Handle user input
# ──────────────────────────────────────────────────────────────────────────────
if prompt := st.chat_input("What can I help you with today?"):
    # Append the user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Invoke the agent
    try:
        with st.spinner("Thinking..."):
            agent = st.session_state.agent_executor
            state = get_state()  # pulls latest (customer_id, is_guest) from backend state

            # Include state in the prompt so tools can use it deterministically
            agent_input = f"{prompt} | customer_id: {state.customer_id} | is_guest: {state.is_guest}"
            response = agent.invoke({"input": agent_input})

        # Agent output text
        agent_response = response.get("output", "Sorry, I ran into an issue.")

        # Try to capture a raw ID pattern as fallback and update backend state if found
        new_id = extract_id_from_response(agent_response)
        if new_id:
            set_customer(new_id)

        # Also accept explicit customer_id in response payload (if a tool returned it)
        if isinstance(response, dict) and "customer_id" in response and response["customer_id"]:
            st.session_state.customer_id = response["customer_id"]

        # Extract FULL URLs if present (preferred), or safe fallbacks
        pp_url, ap_url, pp_token, stripe_id = extract_payment_urls(agent_response)

        # Persist for display/polling
        st.session_state.paypal_url = pp_url
        st.session_state.apple_pay_url = ap_url

        # If the tools also sent IDs in text, store for status checks
        if pp_token:
            st.session_state.paypal_order_id = pp_token
        if stripe_id:
            st.session_state.apple_pay_session_id = stripe_id

        # Start polling if at least one link/ID exists
        if (pp_url or ap_url or pp_token or stripe_id):
            st.session_state.payment_polling = True
            st.session_state.last_payment_check = time.time()

        # Build a single, canonical assistant message (strip any duplicated blocks the LLM wrote)
        cleaned = strip_existing_payment_block(agent_response)
        payment_block = build_payment_block(st.session_state.paypal_url, st.session_state.apple_pay_url)
        assistant_content = (cleaned + ("\n\n" + payment_block if payment_block else "")).strip()

        # Persist assistant message in history (only once)
        st.session_state.messages.append({"role": "assistant", "content": assistant_content or agent_response})

        # Trigger rerun so the message appears via the history loop (prevents double rendering)
        st.rerun()

    except Exception as e:
        error_message = f"An error occurred: {e}"
        st.error(error_message)
        st.session_state.messages.append({"role": "assistant", "content": error_message})
        st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# Background payment status monitoring (lightweight)
# ──────────────────────────────────────────────────────────────────────────────
if st.session_state.payment_polling:
    current_time = time.time()
    # Check every 12 seconds to be gentle on APIs and UI
    if current_time - st.session_state.last_payment_check >= 12:
        st.session_state.last_payment_check = current_time
        try:
            agent = st.session_state.agent_executor

            paypal_id = st.session_state.paypal_order_id
            apple_pay_id = st.session_state.apple_pay_session_id

            # Be explicit: only announce when payment is confirmed/complete
            check_input = (
                "Silently check if payment is completed for "
                f"paypal_order_id: {paypal_id} or apple_pay_session_id: {apple_pay_id}. "
                "Only respond if payment is FULLY COMPLETED and PAID with shipment created; "
                "otherwise respond exactly 'still waiting'."
            )
            check_resp = agent.invoke({"input": check_input})
            payment_response = check_resp.get("output", "")

            # If payment is fully done, post message and stop polling
            if payment_response and payment_response.lower() != "still waiting":
                st.session_state.payment_polling = False
                st.session_state.messages.append({"role": "assistant", "content": payment_response})
                st.rerun()

        except Exception as e:
            logging.warning(f"Payment monitoring error: {e}")

    # Subtle auto-refresh while monitoring
    time.sleep(5)
    st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar indicator/controls for monitoring
# ──────────────────────────────────────────────────────────────────────────────
if st.session_state.payment_polling:
    st.sidebar.markdown("🔄 **Monitoring Payment Status…**")
    st.sidebar.markdown("I'll update you once payment is confirmed and the shipment is created.")
    if st.sidebar.button("Stop Monitoring"):
        st.session_state.payment_polling = False
        st.rerun()
