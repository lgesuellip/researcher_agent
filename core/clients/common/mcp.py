import os
from abc import ABC, abstractmethod
from typing import Any, Optional
from mcp import ClientSession
from mcp.client.stdio import stdio_client

import logging

logger = logging.getLogger(__name__)

class BaseMCPClient(ABC):
    def __init__(
        self,
        server_params: Optional[Any] = None,
        **kwargs: dict[str, Any],
    ) -> None:
        self.session = None
        self._tools: list[Any] = []
        self.server_params = server_params
        self.read: Optional[Any] = None
        self.write: Optional[Any] = None

    @property
    def tools(self) -> list[Any]:
        return self._tools

    async def __aenter__(self):
        self._stdio_ctx = stdio_client(self.server_params)
        self.read, self.write = await self._stdio_ctx.__aenter__()
        
        self.session = ClientSession(self.read, self.write)
        await self.session.__aenter__()
        await self.session.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.__aexit__(exc_type, exc_val, exc_tb)
        if hasattr(self, '_stdio_ctx'):
            await self._stdio_ctx.__aexit__(exc_type, exc_val, exc_tb)
        return 0

    async def init_tools(
        self,
    ) -> None:
        response = await self.session.list_tools()
        self._tools = response.tools

    @abstractmethod
    def wrap_tool(self, name: str, tool_def: Any, **kwargs: Any) -> Any:
        pass

    async def get_tools(
        self, **kwargs: Any
    ) -> list[Any]:
        if not self._tools:
            await self.init_tools()
        return [self.wrap_tool(tool, **kwargs) for tool in self._tools]
