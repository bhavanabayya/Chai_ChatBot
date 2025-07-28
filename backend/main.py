import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.agents import Tool, initialize_agent, AgentType, AgentExecutor, create_tool_calling_agent, create_react_agent
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

from tools.tool_config import get_all_tools
from backend.chat_state import ChatState, ChatStage

# Load .env
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL")

# Initialize the Langchain Agent
def initialize_agent():
    """
    Initializes and returns the Langchain agent executor.
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

    # Define the prompt. Outline behaviour and tools.
    # TODO: Improve this. Correct tool names.
    SYSTEM_PROMPT = """
    You are a friendly and helpful AI assistant for an e-commerce business called Chai Corner.
    Your goal is to help customers find products, add them to a cart, and complete their purchase.
    Be conversational and guide the user step-by-step.

    Here are the tools you have access to:
    {{tools}}

    Follow this process:
    1. Greet the user and ask how you can help.
    2. If the user asks about products, use products_tool.
    3. When the user wants to add a product, use the 'AddToCart' tool.
    4. Before payment, always use 'ViewCart' to confirm the order details and total with the customer.
    5. Once confirmed, use a tool from the PayPal toolkit to generate a payment link.
    6. After the user confirms they have paid, use the 'FinalizeOrder' tool to complete the process.
    7. Do not make up product IDs or prices. Only use the information provided by the tools.

    """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="agent_scratchpad"), # This is where the agent's thought process will be injected
            ("human", "{input}"),
            # ("placeholder", "{chat_history}"), # Can add this for access to past conversations
            # ("placeholder", "{agent_scratchpad}"), # This is where the agent's thought process will be injected
        ]
    )

    # Use models that natively output structured tool calls (JSON)
    # More reliable evolution of the ReAct pattern
    agent = create_tool_calling_agent(llm, tools, prompt)

    # ReAct agents reason about which tool to use and how
    # agent = create_react_agent(llm, tools, prompt)

    # This is the runnable that will execute the agent's decisions.
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

    return agent_executor



# Run the agent with a given query
def run_agent(query: str) -> str:
    """
    Runs the e-commerce agent with the given query and returns the response.
    """
    agent_executor = initialize_agent()
    try:
        response = agent_executor.invoke({"input": query})
        return response.get("output", "I couldn't process that request.")
    except Exception as e:
        return f"An error occurred while processing your request: {e}"
