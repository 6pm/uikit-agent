import asyncio
from datetime import datetime
from typing import Any

from agents.code_generator.state import CodeGenState
from src.logger_config import logger


class MCPContextRetrievalNode:
    """
    Node for retrieving context from MCP servers.

    This node interacts with Model Context Protocol (MCP) servers to fetch
    documentation for identified UI components for both Web and Mobile targets.
    """

    def __init__(self, web_client, mobile_client):
        """
        Initialize the context retrieval node.

        Args:
            web_client: MCP client instance for Web components.
            mobile_client: MCP client instance for Mobile components.
        """
        self.web_client = web_client
        self.mobile_client = mobile_client

    async def retrieve_context(self, state: CodeGenState) -> dict[str, Any]:
        """
        Retrieves documentation for Web and Mobile in parallel.

        Identifies components from the Figma JSON in the state, then queries
        configured MCP servers to get their documentation.

        Args:
            state (CodeGenState): The current state of the execution graph.

        Returns:
            dict[str, Any]: Updates to the state, including 'web_docs' and 'mobile_docs',
            and appends to 'status_history'.
        """

        # 1. Identify components to look up (JSON parsing)
        component_names = self._extract_component_names(state["figma_json"])

        # 2. Create asynchronous tasks
        parallel_tasks = [
            # web
            self._fetch_docs(self.web_client, component_names, "web"),
            # mobile - ensure mobile_client is handled if present
            self._fetch_docs(self.mobile_client, component_names, "mobile"),
        ]

        # 3. Run in parallel
        results = await asyncio.gather(*parallel_tasks, return_exceptions=True)

        web_docs, mobile_docs = results

        # Error handling (if one server fails, the other should still work)
        if isinstance(web_docs, Exception):
            logger.error("Web MCP Error: %s", web_docs)
            web_docs = "Error retrieving Web docs."

        if isinstance(mobile_docs, Exception):
            logger.error("Mobile MCP Error: %s", mobile_docs)
            mobile_docs = "Error retrieving Mobile docs."

        # 4. Return data that will fan out to different graph branches
        return {
            "web_docs": web_docs,
            "mobile_docs": mobile_docs,
            "status_history": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "scope": "common",
                    "status": "success",
                    "message": f"Documentation retrieved from Web {self.mobile_client is not None and 'and Mobile' or ''} sources",
                    "details": None,
                }
            ],
        }

    def _collect_component_names_from_json(self, node: dict, components: set[str]) -> list[str]:
        """
        Recursively traverses Figma JSON to collect component names.

        Args:
            node (dict): The current Figma node being processed.
            components (set[str]): A set to collect unique component names.

        Returns:
            list[str]: The list of component names collected so far (converted from set).
        """

        if node.get("type") == "INSTANCE":
            components.add(node.get("name"))

        if node.get("children"):
            for item in node.get("children"):
                self._collect_component_names_from_json(item, components)

        return list(components)

    def _extract_component_names(self, figma_data: dict) -> list[str]:
        """
        Extracts unique component names from Figma JSON.

        Component names are assumed to be shared between Web and Mobile libraries.

        Args:
            figma_data (dict): The root Figma JSON object.

        Returns:
            list[str]: A list of unique component names found in the design.
        """
        components = set[str]()  # unique component names to fetch docs from MCP
        self._collect_component_names_from_json(figma_data, components)

        return components

    async def call_tool(self, name: str, arguments: dict | None = None) -> Any:
        """
        Call an MCP tool by name on the Web client.

        Args:
            name (str): The name of the tool to call.
            arguments (dict | None): The arguments for the tool.

        Returns:
            Any: The content of the tool result.

        Raises:
            RuntimeError: If the MCP client is not connected.
        """
        if not self.web_client.session:
            raise RuntimeError("MCP Client is not connected")

        if arguments is None:
            arguments = {}

        result = await self.web_client.session.call_tool(name, arguments)
        return result.content

    async def _check_available_components(self, client, components: list[str]) -> tuple[list[str], list[str]]:
        """
        Retrieves the list of available components from MCP and filters the requested ones.

        Args:
            client: The MCP client to query.
            components (list[str]): The list of component names to check.

        Returns:
            tuple[list[str], list[str]]: A tuple containing (available_components, missing_components).
        """
        all_components = await client.session.call_tool("list_components", {})
        known_names = {c.get("name") for c in all_components.structuredContent.get("components")}

        available = []
        missing = []
        for c in components:
            if c in known_names:
                available.append(c)
            else:
                missing.append(c)

        return available, missing

    async def _fetch_docs(self, client, components: list[str], source_type: str) -> str:
        """
        Helper method to fetch documentation from an MCP client.

        Args:
            client: The MCP client to use.
            components (list[str]): List of component names to fetch docs for.
            source_type (str): Identifier for the source (e.g., 'web', 'mobile') for logging.

        Returns:
            str: The aggregated documentation text, or None if client is invalid.
        """
        if not client:
            return None

        available_components, missing_components = await self._check_available_components(client, components)

        if missing_components:
            logger.warning("Missing components in %s: %s", source_type, missing_components)

        docs = []
        for comp in available_components:
            # Call the specific tool provided by the MCP server, e.g., "get_component_doc"
            try:
                result = await client.session.call_tool("get_component_doc", {"componentName": comp})
                docs.append(f"### {comp} \n{result.structuredContent.get('documentation')}")
            except Exception as e:
                logger.warning("Failed to fetch %s from %s: %s", comp, source_type, e)

        return "\n".join(docs)
