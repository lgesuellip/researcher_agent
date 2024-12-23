from typing import Any, Callable
import logging
from langchain_core.tools import StructuredTool
from ..common.mcp import BaseMCPClient
from ..common.utils import create_pydantic_model_from_json_schema
import asyncio
logger = logging.getLogger(__name__)

class LanggraphMCPClient(BaseMCPClient):

    def tool_call(self, tool_name: str) -> Any:

        async def tool_function(*args: Any, **kwargs: Any) -> Any:
            print(f"Executing toolwith args: {args} and kwargs: {kwargs}, {tool_name}")
            result = await self.session.call_tool(tool_name, arguments=kwargs)
            return result
        
        return tool_function

    def wrap_tool(
        self, tool: Any, **kwargs: Any
    ) -> StructuredTool:
        """Wrap a tool as a CrewAI StructuredTool.

        Args:
            tool_name: The name of the tool to wrap.
            tool_definition: The definition of the tool to wrap.
            **kwargs: Additional keyword arguments for tool configuration.

        Returns:
            A StructuredTool instance.
        """

        return StructuredTool.from_function(
            coroutine=self.tool_call(tool.name),
            name=tool.name,
            description=tool.description or "No description provided.",
            args_schema=create_pydantic_model_from_json_schema(tool.name, tool.inputSchema),
        )
