from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from contextlib import asynccontextmanager
from langchain_mcp_adapters.client import MultiServerMCPClient

import os

from dotenv import load_dotenv

load_dotenv()

@asynccontextmanager
async def build_agent():

    tools = []
    
    servers = {}
    
    zapi_url = os.getenv("ZAPIER_URL_MCP")
    if zapi_url:
        servers["zapi"] = {
            "url": zapi_url,
            "transport": "sse",
        }

    async with MultiServerMCPClient(servers) as client:
        tools = client.get_tools()
        model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
        )

        graph = create_react_agent(model, tools=tools)
        
        yield graph
