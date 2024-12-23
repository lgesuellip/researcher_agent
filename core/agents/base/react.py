from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from mcp import StdioServerParameters
from clients.langgraph.client import LanggraphMCPClient

from langchain_arcade import ArcadeToolManager

import asyncio
import logging

import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logger.info("Starting the example client script.")

server_params = StdioServerParameters(
    command="uv",
    args= [
        "--directory",
        "/Users/lgesuellip/Desktop/mcp_firecrawl/researcher_service/servers",
        "run",
        "website-firecrawl-service"
    ]
)

async def main():

    tools = []

    # Get tools from MCP
    async with LanggraphMCPClient(server_params=server_params) as mcp_client:
        tools.extend(await mcp_client.get_tools())
    
        # Get tools from Arcade
        tool_arcade_manager = ArcadeToolManager(api_key=os.getenv("ARCADE_API_KEY"))
        tools.extend(tool_arcade_manager.get_tools(toolkits=["slack"]))
    
        model = ChatOpenAI(model="gpt-4")

        graph = create_react_agent(model, tools=tools)

        inputs = {
            "messages": [HumanMessage(content="A summary of pampa.ai website, and send it to 'lautaro'")],
        }

        config = {
            "configurable": {
                "thread_id": "1",
                "user_id": os.getenv("ARCADE_USER_ID"),
            }
        }
        result = await graph.ainvoke(inputs, config=config)
        print(result)

if __name__ == "__main__":
    asyncio.run(main())



