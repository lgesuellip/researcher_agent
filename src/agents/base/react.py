from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from contextlib import asynccontextmanager
from langchain_mcp_adapters.client import MultiServerMCPClient

import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logger.info("Starting the example client script.")

@asynccontextmanager
async def build_agent():

    tools = []
    
    # Create servers dictionary only with available URLs
    servers = {}
    
    calendar_url = os.getenv("CALENDAR_URL_MCP")
    if calendar_url:
        servers["calendar"] = {
            "url": calendar_url,
            "transport": "sse",
        }
    
    firecrawl_url = os.getenv("FIRECRAWL_URL_MCP")
    if firecrawl_url:
        servers["firecrawl"] = {
            "url": firecrawl_url,
            "transport": "sse",
        }
    
    async with MultiServerMCPClient(servers) as client:
        tools = client.get_tools()
        model = ChatOpenAI(
            model="o3-mini",
            reasoning_effort="medium",
        )

        graph = create_react_agent(model, tools=tools)
        
        yield graph
