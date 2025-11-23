import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph

from agents.code_generator.state import CodeGenState
from schemas.api.code_generation_types import CodeGenerationRequest

from .nodes import CodeGenNodes
from .prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class CodeGeneratorAgent:
    """
    Orchestrator - knows how to set up the system (which model to take, which temperature to set).
    It is responsible for initializing the system and launching the agent.
    """

    def __init__(self):
        """Initialize agent with default values."""
        self.graph = None
        self.gemini_model = None

    async def _initialize(self):
        """
        Async initialization method.
        """
        await self.init_gemini_model()
        await self.build_graph()

    @classmethod
    async def create(cls):
        """
        Factory method for async initialization.
        """
        instance = cls()
        await instance._initialize()
        return instance

    async def init_gemini_model(self):
        """
        Initialize Gemini model.
        У майбутньому буде декілька класів з нодами (ValidationNodes, RefactoringNodes).
        Краще створити один екземпляр моделі в Оркестраторі і роздати його всім нодам,
        ніж кожна нода буде створювати своє з'єднання.
        """
        self.gemini_model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0,
            max_retries=2,
        )

    async def build_graph(self):
        """
        Build the StateGraph for code generation.
        """
        # Initialize nodes with the model
        nodes = CodeGenNodes(self.gemini_model)

        # Set up Graph Builder with State
        # We use our custom CodeGenState
        graph_builder = StateGraph[CodeGenState, None, CodeGenState, CodeGenState](CodeGenState)

        # Add nodes
        # We pass the method from our nodes instance
        graph_builder.add_node("generate_code", nodes.call_model)

        # Build flow
        graph_builder.add_edge(START, "generate_code")
        graph_builder.add_edge("generate_code", END)

        self.graph = graph_builder.compile()

    async def generate_code(self, request_data: CodeGenerationRequest) -> dict[str, Any]:
        """
        Generate code from Figma JSON data using LangGraph.
        This is main function for launching the agent.
        As a result it will return generated code and status of the task.

        Returns:
            dict[str, Any]: Dictionary with generated code and status of the task
        """
        # Convert request to JSON string
        message_str = request_data.model_dump_json()

        # Initialization of messages, system prompt and status
        inputs = {
            "messages": [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=message_str)],
            "status": "pending",
        }

        # Invoke graph
        result = await self.graph.ainvoke(inputs)

        # Get last message
        last_message = result["messages"][-1]

        return {"content": last_message.content, "status": result.get("status")}
