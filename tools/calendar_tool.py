from langchain_core.tools import tool

@tool
def schedule_meeting(details: str) -> str:
    """
    Simulates scheduling a meeting and generating a Google Calendar link.
    """
    calendar_link = f"https://calendar.google.com/event?details={details.replace(' ', '_')}"
    return f" Meeting scheduled for: {details}\nHere is your calendar link: {calendar_link}"

calendar_tool = schedule_meeting
