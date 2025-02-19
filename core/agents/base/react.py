from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from mcp import StdioServerParameters
from mcp import ClientSession, StdioServerParameters

from mcp.client.stdio import stdio_client

from langchain_mcp_adapters.tools import load_mcp_tools

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
        "/Users/lgesuellip/Desktop/mcp_firecrawl/researcher_agent/servers",
        "run",
        "website-firecrawl-service"
    ]
)

async def main():

    tools = []

    # Get tools from MCP
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools.extend(await load_mcp_tools(session))
    
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



