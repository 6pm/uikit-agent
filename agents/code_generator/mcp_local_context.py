"""
Module for interacting with a local JSON file as if it were an MCP server.
Provides a mock client that reads component documentation from a local file.
"""

import json
import os
from dataclasses import dataclass, field

from app.utils.logger_config import logger


@dataclass
class TextContent:
    type: str = "text"
    text: str = ""


@dataclass
class ToolResult:
    content: list[TextContent] = field(default_factory=list)
    structuredContent: dict = field(default_factory=dict)
    isError: bool = False


class MockSession:
    """
    Mock session that simulates MCP ClientSession behavior but reads from a local file.
    """

    def __init__(self, context_file_path: str):
        self.context_file_path = context_file_path
        self._data = {}
        self._load_data()

    def _load_data(self):
        """Loads data from the context file."""
        if not os.path.exists(self.context_file_path):
            logger.warning(f"Context file not found: {self.context_file_path}")
            return

        try:
            with open(self.context_file_path, encoding="utf-8") as f:
                self._data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading context file {self.context_file_path}: {e}")
            self._data = {}

    async def call_tool(self, name: str, arguments: dict) -> ToolResult:
        """
        Simulates calling a tool.
        """
        if name == "list_components":
            # Return keys from the object that have non-empty values
            keys = [k for k, v in self._data.items() if v]
            components_list = [{"name": k} for k in keys]
            return ToolResult(
                content=[TextContent(text=json.dumps(keys))],
                structuredContent={"components": components_list},
            )

        elif name == "get_component_doc":
            comp_name = arguments.get("componentName") or arguments.get("name")
            if not comp_name:
                return ToolResult(
                    isError=True,
                    content=[TextContent(text="Missing componentName argument")],
                )

            # Retrieve the component doc by key
            doc = self._data.get(comp_name)
            if doc:
                # Ensure doc is returned as string
                text_content = doc if isinstance(doc, str) else json.dumps(doc)
                return ToolResult(
                    content=[TextContent(text=text_content)],
                    structuredContent={"documentation": text_content},
                )
            else:
                return ToolResult(
                    isError=True,
                    content=[TextContent(text=f"Component '{comp_name}' not found")],
                )

        return ToolResult(isError=True, content=[TextContent(text=f"Tool '{name}' not found")])

    async def initialize(self):
        """Mock initialize method."""
        pass


class MCPLocalContextClient:
    """
    Client for interacting with a local context file, mimicking an MCP client.
    """

    def __init__(self, context_file_path: str):
        """
        Initialize MCP Local Context Client.

        Args:
            context_file_path: Path to the file with JSON documentation.
        """
        self.context_file_path = context_file_path
        self.session: MockSession | None = None

    async def connect(self):
        """
        Initialize connection (load file).
        """
        self.session = MockSession(self.context_file_path)
        logger.info(f"Connected to local context file: {self.context_file_path}")

    async def call_tool(self, name: str, arguments: dict) -> str:
        """
        Executes a tool on the mock session and returns the text content.
        Compatible with MCPClient.call_tool signature.
        """
        if not self.session:
            return f"Error: Session not initialized for tool {name}"

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
        """Automatically called on exit."""
        await self.close()

    async def close(self):
        """Cleanup resources."""
        self.session = None
        logger.info("Closed local context connection")
