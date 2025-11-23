"""
Agent task which run code generation using LangGraph
"""
import json
from schemas.api.code_generation_types import CodeGenerationRequest
from schemas.ai_models.test_ai_response import TestAIResponse
from typing import Any, Dict
import logging

from langgraph.graph import END, START, MessagesState, StateGraph


logger = logging.getLogger(__name__)


def mock_llm(state: MessagesState) -> TestAIResponse:
    print("state mock_llm", state)
    return {"messages": [{"role": "ai", "content": "hello world and Slava"}]}


class CodeGeneratorAgent:
    def __init__(self):
        """Initialize agent with default values."""

        self.graph = None

    async def _initialize(self):
        """
        Async initialization method.
        Call this after creating the instance if you need async setup.
        """
        # Example: async initialization logic here
        # await self._setup_llm()
        # await self._setup_tools()

        await self.build_graph()

    @classmethod
    async def create(cls):
        """
        Factory method for async initialization.

        Usage:
            agent = await CodeGeneratorAgent.create()

        Returns:
            CodeGeneratorAgent: Initialized agent instance
        """
        instance = cls()
        await instance._initialize()
        return instance

    async def build_graph(self):
        """
        Generate code from Figma JSON

        Args:
            json_data: Figma JSON

        Returns:
            dict: Code generation result
        """

        # Set up Graph Builder with State
        graph_builder = StateGraph(MessagesState)

        # test mock code
        graph_builder.add_node(mock_llm)
        graph_builder.add_edge(START, "mock_llm")
        graph_builder.add_edge("mock_llm", END)
        # end test mock code

        # # Add nodes
        # graph_builder.add_node("worker", self.worker)
        # graph_builder.add_node("tools", ToolNode(tools=self.tools))
        # graph_builder.add_node("evaluator", self.evaluator)

        # # Add edges
        # graph_builder.add_conditional_edges(
        #     "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
        # )
        # graph_builder.add_edge("tools", "worker")
        # graph_builder.add_conditional_edges(
        #     "evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END}
        # )
        # graph_builder.add_edge(START, "worker")

        # # Compile the graph
        # self.graph = graph_builder.compile(checkpointer=self.memory)

        self.graph = graph_builder.compile()

    async def generate_code(self, request_data: CodeGenerationRequest) -> Dict[str, Any]:
        """
        Generate code from Figma JSON data.

        Args:
            json_data: Dictionary containing request data (components, framework, etc.)

        Returns:
            Dictionary with generation results
        """
        # BEST PRACTICE: Convert dict to JSON string for LangGraph message content
        # LangGraph's HumanMessage expects content to be a string or list, not a dict
        message_str = request_data.model_dump_json()

        result = await self.graph.ainvoke({"messages": [{"role": "user", "content": message_str}]})

        return result
