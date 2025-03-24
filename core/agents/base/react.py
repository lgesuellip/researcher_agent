from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from contextlib import asynccontextmanager
from langchain_mcp_adapters.client import MultiServerMCPClient

import asyncio
import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logger.info("Starting the example client script.")

import subprocess
import sys

def install_uv():
    try:
        subprocess.run(
            ["curl", "-Ls", "https://astral.sh/uv/install.sh", "-o", "install_uv.sh"],
            check=True
        )
        subprocess.run(
            ["sh", "install_uv.sh"],
            check=True
        )
        print("✅ uv installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install uv: {e}")
        sys.exit(1)

install_uv()

@asynccontextmanager
async def build_agent():
    install_uv()
    # Get the absolute path to the servers directory
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    servers_dir = os.path.join(base_dir, "servers")
    print(servers_dir)
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
                    servers_dir,
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
