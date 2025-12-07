import os
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.logger_config import logger


class MCPClient:
    """
    Client for interacting with Model Context Protocol (MCP) servers.
    Handles connection management and tool retrieval.
    """

    def __init__(self, server_script_path: str):
        """
        Initialize MCP Client.

        Args:
            server_script_path: Path to the MCP server script (Node.js)
        """
        self.server_script_path = server_script_path
        self.session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()
        self.tools = []

    async def connect(self):
        """
        Initialize MCP connection to local Node.js server.
        """
        if not os.path.exists(self.server_script_path):
            logger.warning(
                "MCP server script not found at %s. Skipping MCP initialization.",
                self.server_script_path,
            )
            return

        server_params = StdioServerParameters(command="node", args=[self.server_script_path], env=os.environ.copy())

        try:
            # Start the client
            read, write = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            await self.session.initialize()

            # Get tools
            result = await self.session.list_tools()
            self.tools = result.tools
            logger.info("Connected to MCP server. Found %d tools.", len(self.tools))

        except Exception as e:
            logger.error("Failed to initialize MCP: %s", e, exc_info=True)
            await self.close()

    def get_langchain_tools(self) -> list[dict[str, Any]]:
        """
        Convert loaded MCP tools to LangChain tool format.

        Returns:
            List of tools in LangChain format (name, description, parameters)
        """
        langchain_tools = []
        for tool in self.tools:
            langchain_tools.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                }
            )
        return langchain_tools

    async def close(self):
        """Cleanup resources."""
        await self.exit_stack.aclose()
