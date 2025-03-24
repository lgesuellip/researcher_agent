from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from contextlib import asynccontextmanager
from langchain_mcp_adapters.client import MultiServerMCPClient

import asyncio
import logging

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logger.info("Starting the example client script.")


@asynccontextmanager
async def build_agent():

    tools = []
    async with MultiServerMCPClient(
        {
            "slack": {
                "url": "https://actions.zapier.com/mcp/sk-ak-WXJtdTT4eJntUOY8OlsIDYYaSJ/sse",
                "transport": "sse",
            },
            "researcher": {
                "command": "uv",
                "args": [
                    "--directory",
                    "/Users/lgesuellip/Desktop/mcp_firecrawl/researcher_agent/servers",
                    "run",
                    "website-firecrawl-service"
                ],
                "transport": "stdio"
            }
        }
    ) as client:
    
            tools = client.get_tools()
            model = ChatOpenAI(model="gpt-4")

            graph = create_react_agent(model, tools=tools)
            
            yield graph

