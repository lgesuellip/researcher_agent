import os
from abc import ABC, abstractmethod
from typing import Any, Optional
from mcp import ClientSession
from mcp.client.stdio import stdio_client

import logging

logger = logging.getLogger(__name__)

class BaseMCPClient(ABC):
    """Abstract base class for MCP clients providing session management and tool handling."""

    def __init__(
        self,
        server_params: Optional[Any] = None,
        **kwargs: dict[str, Any],
    ) -> None:
        """
        Initialize the BaseMCPClient with optional server parameters.

        Args:
            server_params: Optional parameters for server configuration.
            **kwargs: Additional keyword arguments.
        """
        self.session = None
        self._tools: list[Any] = []
        self.server_params = server_params
        self.read: Optional[Any] = None
        self.write: Optional[Any] = None

    @property
    def tools(self) -> list[Any]:
        """List of tools available to the client."""
        return self._tools

    async def __aenter__(self):
        """
        Asynchronous context manager entry.

        Initializes the stdio client and session, preparing the client for use.
        """
        self._stdio_ctx = stdio_client(self.server_params)
        self.read, self.write = await self._stdio_ctx.__aenter__()
        
        self.session = ClientSession(self.read, self.write)
        await self.session.__aenter__()
        await self.session.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Asynchronous context manager exit.

        Cleans up the session and stdio context.
        """
        if self.session:
            await self.session.__aexit__(exc_type, exc_val, exc_tb)
        if hasattr(self, '_stdio_ctx'):
            await self._stdio_ctx.__aexit__(exc_type, exc_val, exc_tb)
        return 0

    async def init_tools(
        self,
    ) -> None:
        """
        Initialize the list of tools by querying the session.

        Populates the internal tools list with available tools from the session.
        """
        response = await self.session.list_tools()
        self._tools = response.tools

    @abstractmethod
    def wrap_tool(self, name: str, tool_def: Any, **kwargs: Any) -> Any:
        """
        Abstract method to wrap a tool definition.

        Args:
            name: The name of the tool.
            tool_def: The tool definition object.
            **kwargs: Additional keyword arguments for tool configuration.

        Returns:
            A wrapped tool object.
        """
        pass

    async def get_tools(
        self, **kwargs: Any
    ) -> list[Any]:
        """
        Retrieve and wrap available tools.

        Args:
            **kwargs: Additional keyword arguments for tool wrapping.

        Returns:
            A list of wrapped tool objects.
        """
        if not self._tools:
            await self.init_tools()
        return [self.wrap_tool(tool, **kwargs) for tool in self._tools]
