import logging
import re
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

@tool
def generate_summary(order_text: str) -> str:
    """
    Parses a chai/coffee order like '2 masala chai and 1 ginger chai'
    and returns a summary with itemized costs and estimated total.
    """
    logger.info(f"Executing generate_summary tool for order text: '{order_text}'")

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
        
        if matches:
            logger.debug(f"Found matches for '{item}': {matches}")

        for match in matches:
            try:
                quantity = int(match) if match else 1
                subtotal = quantity * price
                total += subtotal
                summary_lines.append(f"{quantity} {item.title()} - ${subtotal:.2f}")
                logger.info(f"Item detected: {quantity} of '{item}'. Subtotal: ${subtotal:.2f}")
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to parse quantity for item '{item}' from match '{match}': {e}", exc_info=True)
                continue

    if not summary_lines:
        logger.warning(f"No valid items were detected in the order text: '{order_text}'")
        return "Sorry, I couldn't detect any valid items in your order."
    
    final_summary = "\n".join(summary_lines) + f"\n\n**Estimated Total:** ${total:.2f}"
    logger.info(f"Generated order summary. Estimated total: ${total:.2f}")
    
    return final_summary