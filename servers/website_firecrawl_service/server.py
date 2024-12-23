import logging
from typing import List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
from mcp.types import ServerCapabilities

from .crawler import WebsiteCrawler
from website_firecrawl_service.utils import clean_html_text


load_dotenv()

server = Server("website_firecrawl_service")

class WebsiteCrawlArgs(BaseModel):
    query: str
    base_url: str
    max_links: int = 100

    model_config = {
        "json_schema_extra": {
            "description": "Arguments for crawling a website"
        }
    }

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    return [
        types.Tool(
            name="website_firecrawl",
            description="Crawl a website",
            inputSchema=WebsiteCrawlArgs.model_json_schema(),
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Optional[dict]
) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    
    Args:
        name: The name of the tool to execute
        arguments: Dictionary of tool arguments
        
    Returns:
        List of content items produced by the tool
        
    Raises:
        ValueError: If tool name is invalid or arguments are missing
    """
    try:
        if name != "website_firecrawl":
            raise ValueError(f"Unknown tool: {name}")

        if not arguments:
            raise ValueError("Missing arguments")
        
        args = WebsiteCrawlArgs.model_validate(arguments)

        logging.info(f"Starting crawl of query={args.query} and base_url={args.base_url} with max_links={args.max_links}")
        
        crawler = WebsiteCrawler()
        pages = await crawler.crawl(args.query, args.base_url, args.max_links, llm_predict=True)

        return [
            types.TextContent(
                type="text",
                text="\n".join(clean_html_text(str(page)) for page in pages),
            )
        ]
    except Exception as e:
        logging.error(f"Error during crawl: {str(e)}")
        raise

async def main():
    logging.basicConfig(level=logging.INFO)
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        try:
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=server.name,
                    server_version="0.1.0",
                    capabilities=ServerCapabilities()
                )
            )
        except Exception as e:
            logging.error(f"Server error: {str(e)}")
            raise
