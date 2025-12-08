"""Code Generator Agent - orchestrates the code generation workflow."""

from huey.utils import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph

from agents.code_generator.state import CodeGenState
from src.logger_config import logger

from .mcp_client import MCPClient
from .nodes import (
    InputValidationNodes,
    MCPContextRetrievalNode,
    MobileCodeGenNode,
    WebCodeGenNode,
)


class CodeGeneratorAgent:
    """
    Orchestrator - knows how to set up the system (which model to take, which temperature to set).
    It is responsible for initializing the system and launching the agent.
    """

    def __init__(self):
        """Initialize agent with default values."""
        self.graph = None
        self.gemini_model = None

        # configure MCP clients
        self.mcp_web_client = MCPClient("node_modules/@patrianna/uikit/dist/mcp-server/server.js")
        self.mcp_mobile_client = None

    async def __aenter__(self):
        """
        Resource initialization when entering the 'async with' block.
        We don't use __init__ because we want to use the context manager pattern.
        """
        # 1. Connect MCP clients (either via exit stack or manual enter)
        # Here we cascade the aenter calls for clients
        await self.mcp_web_client.__aenter__()
        if self.mcp_mobile_client:
            await self.mcp_mobile_client.__aenter__()

        # 2. Initialize the model
        await self.init_gemini_model()

        # 3. Build the graph (safe now because MCPs are connected)
        await self.build_graph()

        return self

    async def init_gemini_model(self):
        """
        Initialize Gemini model.
        In the future there will be several node classes (ValidationNodes, RefactoringNodes).
        It is better to create one model instance in the Orchestrator and share it with all nodes,
        rather than having each node create its own connection.
        """
        self.gemini_model = ChatGoogleGenerativeAI(
            model=os.getenv("MODEL_CODEGEN") or "gemini-2.5-pro",
            temperature=0.2,
            max_retries=2,
        )

    async def build_graph(self):
        """
        Builds the Directed Acyclic Graph (DAG) for code generation.
        Includes stages: Validation -> Context -> (Web | Mobile) -> Linters -> Finish.
        """
        # 1. Initialize all nodes with dependencies
        input_nodes = InputValidationNodes()

        # Pass both MCP clients
        mcp_nodes = MCPContextRetrievalNode(web_client=self.mcp_web_client, mobile_client=self.mcp_mobile_client)

        # Pass the model (can bind tools if needed, but we use MCP separately)
        web_codegen_node = WebCodeGenNode(self.gemini_model)
        mobile_codegen_node = MobileCodeGenNode(self.gemini_model)

        # 2. Create graph with typed state
        workflow = StateGraph(CodeGenState)

        # --- Add Nodes ---

        # Common stages for all flows: web and mobile
        workflow.add_node("validate_input", input_nodes.validate_input)
        workflow.add_node("retrieve_mcp_context", mcp_nodes.retrieve_context)

        # Web Branch
        workflow.add_node("generate_web", web_codegen_node.generate_code)
        workflow.add_node("lint_web", web_codegen_node.run_linter)

        # Mobile Branch
        workflow.add_node("generate_mobile", mobile_codegen_node.generate_code)
        workflow.add_node("lint_mobile", mobile_codegen_node.run_linter)

        # --- Build Edges between nodes ---

        # Start -> Validation phase
        workflow.add_edge(START, "validate_input")

        # Conditional edge: If validation fails - END, otherwise - MCP context retrieval
        workflow.add_conditional_edges(
            "validate_input",
            input_nodes.should_continue,  # Function deciding whether to proceed or stop if validation fails
            {  # Map: {function_return: destination}
                "retrieve_mcp_context": "retrieve_mcp_context",
                END: END,
            },
        )

        # FORK: After context, run both branches in parallel
        workflow.add_edge("retrieve_mcp_context", "generate_web")
        workflow.add_edge("retrieve_mcp_context", "generate_mobile")

        # # Web Chain
        workflow.add_edge("generate_web", "lint_web")
        workflow.add_edge("lint_web", END)

        # # Mobile Chain
        workflow.add_edge("generate_mobile", "lint_mobile")
        workflow.add_edge("lint_mobile", END)

        # 3. Compile LangGraph workflow graph
        self.graph = workflow.compile()
        logger.info("CodeGen Graph built successfully.")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Clean up resources from MCP clients.
        Automatically called when exiting the 'async with' block.

        This guarantees that the Node.js process is terminated immediately
        after use (JIT strategy), releasing RAM.

        It runs regardless of whether the block finished successfully
        or raised an exception.
        """
        if self.mcp_web_client:
            await self.mcp_web_client.__aexit__(exc_type, exc_val, exc_tb)
        if self.mcp_mobile_client:
            await self.mcp_mobile_client.__aexit__(exc_type, exc_val, exc_tb)

        logger.info("Agent resources released from MCP clients.")
