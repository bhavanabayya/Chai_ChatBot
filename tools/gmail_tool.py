from langchain_core.tools import tool

dummy_meeting_link = "https://calendar.google.com/event?eid=dummy-followup"

@tool
def schedule_followup(email: str) -> str:
    """
    Schedule a follow-up meeting via Google Calendar and send a confirmation email.
    """
    
    return f"📅 Follow-up meeting scheduled. Confirmation sent to {email}. View event: {dummy_meeting_link}"

gmail_tool = schedule_followup
