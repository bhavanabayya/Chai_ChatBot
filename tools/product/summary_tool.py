from langchain_core.tools import tool
import re

@tool
def generate_summary(order_text: str) -> str:
    """
    Parses a chai/coffee order like '2 masala chai and 1 ginger chai'
    and returns a summary with itemized costs and estimated total.
    """
    items = {
        "masala chai": 20,
        "ginger chai": 15,
        "elaichi chai": 16,
        "madras coffee": 20
    }
    total = 0
    summary_lines = []

    for item, price in items.items():
        pattern = rf"(?:(\d+)\s*)?{re.escape(item)}"
        matches = re.findall(pattern, order_text.lower())

        for match in matches:
            quantity = int(match) if match else 1
            subtotal = quantity * price
            total += subtotal
            summary_lines.append(f"{quantity} x {item.title()} - ${subtotal:.2f}")

    if not summary_lines:
        return "Sorry, I couldn't detect any valid items in your order."

    return "\n".join(summary_lines) + f"\n\n**Estimated Total:** ${total:.2f}"
