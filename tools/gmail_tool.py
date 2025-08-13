from langchain_core.tools import tool

dummy_meeting_link = "https://calendar.google.com/event?eid=dummy-followup"

@tool
def schedule_followup(email: str) -> str:
    """
    Schedule a follow-up meeting via Google Calendar and send a confirmation email.
    """
    
    return f"Follow-up meeting scheduled. Confirmation sent to {email}. View event: {dummy_meeting_link}"

gmail_tool = schedule_followup
# from langchain_core.tools import tool
# import base64
# from email.message import EmailMessage
# import os
# import json
# import requests

# @tool
# def email_invoice_tool(input_text: str) -> str:
#     """
#     Email the latest invoice PDF to the customer.
#     Format: "Send invoice invoice_1072.pdf to user@example.com"
#     """
#     import re
#     match = re.search(r"invoice_(\d+)\.pdf.*to\s+(\S+@\S+)", input_text)
#     if not match:
#         return " Could not parse invoice ID or email address."
    
#     invoice_id, email = match.groups()
#     pdf_path = os.path.join("invoices", f"invoice_{invoice_id}.pdf")
#     if not os.path.exists(pdf_path):
#         return " Invoice file not found."

#     message = EmailMessage()
#     message["To"] = email
#     message["From"] = "me"
#     message["Subject"] = f"Your Chai Corner Invoice #{invoice_id}"
#     message.set_content("Hi! Please find your invoice attached.")

#     with open(pdf_path, "rb") as f:
#         content = f.read()
#         message.add_attachment(content, maintype="application", subtype="pdf", filename=f"invoice_{invoice_id}.pdf")

#     encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
#     access_token = os.getenv("GMAIL_ACCESS_TOKEN")
#     headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
#     body = json.dumps({"raw": encoded_message})

#     res = requests.post("https://gmail.googleapis.com/gmail/v1/users/me/messages/send", headers=headers, data=body)
#     if res.status_code == 200:
#         return f"Invoice sent to {email}"
#     else:
#         return f"Failed to send email: {res.status_code} - {res.text}"
