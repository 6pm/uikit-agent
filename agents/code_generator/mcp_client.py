"""
Module for interacting with Model Context Protocol (MCP) servers.
Handles connection management using Async Context Manager pattern.
"""

import os
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.logger_config import logger


class MCPClient:
    """
    Client for interacting with Model Context Protocol (MCP) servers.
    Handles connection management using Async Context Manager pattern.
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
        self._command = "node"

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

        server_params = StdioServerParameters(command=self._command, args=[self.server_script_path], env=os.environ.copy())

        try:
            # Start the client within the exit stack
            read, write = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            await self.session.initialize()

            # Get tools
            result = await self.session.list_tools()
            self.tools = result.tools
            logger.info("Connected to MCP server. Found %d tools.", len(self.tools))

        except Exception as e:
            logger.error("Failed to initialize MCP: %s", e, exc_info=True)
            # Do not call close() here to avoid breaking the stack; the error will propagate up
            raise e

    async def call_tool(self, name: str, arguments: dict) -> str:
        """Executes a tool on the MCP server."""
        if not self.session:
            # If there is no session, return an empty string or error,
            # but do not crash the entire process
            return f"Error: MCP Session not initialized for tool {name}"

        try:
            result = await self.session.call_tool(name, arguments)
            if result.content and len(result.content) > 0:
                return result.content[0].text
            return ""
        except Exception as e:
            logger.error("Error calling tool %s: %s", name, e)
            return f"Error executing tool {name}: {e}"

    # --- Context Manager Protocol ---
    async def __aenter__(self):
        """Automatically called when entering 'async with'."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Automatically called on exit, even if an error occurred."""
        await self.close()

    async def close(self):
        """Cleanup resources properly."""
        logger.info("Closing MCP connection...")
        try:
            await self.exit_stack.aclose()
        except Exception as e:
            # Log but do not raise cleanup error, to avoid masking the main error
            logger.warning("Error during MCP cleanup: %s", e)
