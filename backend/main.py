import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

from tools.tool_config import get_all_tools

# Load .env
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL")

# Create the Langchain Agent
def create_agent():
    """
    Creates and returns the Langchain agent executor.
    This function should only be called ONCE per user session.
    Its state (including memory) is maintained by Streamlit's session_state.
    """
    
    # Get all the tools that are available for the agent to use:
    tools = get_all_tools()
        
    # Define the LLM to be used by the agent
    # Keep temperature at 0 to keep responses to reduce randomness
    # gpt-4o vs gpt-4-turbo: gpt-4o is faster and cheaper (twice as fast, half as expensive)
    llm = ChatOpenAI(
        model = OPENAI_API_MODEL,
        temperature = 0,
        openai_api_key = OPENAI_API_KEY
    )

    memory = ConversationBufferMemory(
        memory_key="chat_history", 
        return_messages=True
    )

    # Define the prompt. Outline behaviour and tools.
    # TODO: Improve this. Correct tool names.
    SYSTEM_PROMPT = """
    You are a friendly and helpful AI assistant for an e-commerce business called Chai Corner.
    Your goal is to help customers find products, add them to a cart, and complete their purchase.
    Be conversational and guide the user step-by-step. Do not make up product IDs or prices. Only use the information provided by the tools.

    Here are the tools you have access to:
    {{tools}}

    Follow this process:
    1. Greet the user and ask how you can help.
    2. If the user asks about products, use products_tool.
    3. Use the cart tools when user wants to add or remove items from their order, view cart and clear cart.
    4. Generate an invoice and give the pdf to the customer for customer 58 using invoice_tool (Use the format: 'Generate 2 Madras Coffee and 1 Cardamom Chai for customer 58' to interface with the tool). Convert the pdf that is saved to an image and show it to the customer, so that the customer can verify everything is correct.
    5. Once confirmed, use a tool from the PayPal toolkit to generate a payment link for the order. Use order tools to keep track of order ID.
    6. Once the customer says that they have paid, use the order number to confirm that they have indeed done so. Output the details to the customer
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"), # This is where the agent's thought process will be injected
        ]
    )

    # Use models that natively output structured tool calls (JSON)
    # More reliable evolution of the ReAct pattern
    agent = create_tool_calling_agent(llm, tools, prompt)
    

    # This is the runnable that will execute the agent's decisions.
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        memory=memory, 
        verbose=True, 
        handle_parsing_errors=True
    )

    return agent_executor
