"""Code Generator Agent - orchestrates the code generation workflow."""

from typing import Literal

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph

from agents.code_generator.mcp_client import MCPClient
from agents.code_generator.mcp_local_context import MCPLocalContextClient
from agents.code_generator.nodes.input_validation import InputValidationNodes
from agents.code_generator.nodes.mcp_context_retrieval import MCPContextRetrievalNode
from agents.code_generator.nodes.mobile_nodes import MobilePipelineNodes
from agents.code_generator.nodes.web_nodes import WebPipelineNodes
from agents.code_generator.state import CodeGenState
from app.core.settings import settings
from app.services.repository_workspace import RepositoryWorkspace
from app.services.status_reporter import StatusReporter
from app.utils.logger_config import logger


class CodeGeneratorAgent:
    """
    Orchestrator - knows how to set up the system (which model to take, which temperature to set).
    It is responsible for initializing the system and launching the agent.
    """

    def __init__(self, task_id: str):
        """Initialize agent with default values."""
        self.graph = None
        self.gemini_model = None

        # configure MCP clients
        self.mcp_web_client = MCPClient("node_modules/@patrianna/uikit/dist/mcp-server/server.js")
        # TODO: temporary solution with local file for mobile client
        self.mcp_mobile_client = MCPLocalContextClient(f"{settings.MOBILE_REPO_PATH}/dist/components/ui/ai-docs.json")

        self.task_id = task_id

        # classes to work with repositories - clone, update files, commit.
        self.web_workspace = RepositoryWorkspace(
            repo_url=settings.WEB_REPO_URL,
            local_path=settings.WEB_REPO_PATH,
            git_ssh_key_path=settings.GIT_SSH_KEY_PATH,
        )
        self.mobile_workspace = RepositoryWorkspace(
            repo_url=settings.MOBILE_REPO_URL,
            local_path=settings.MOBILE_REPO_PATH,
            git_ssh_key_path=settings.GIT_SSH_KEY_PATH,
        )

    async def __aenter__(self):
        """
        Resource initialization when entering the 'async with' block(Heavyweight).
        We don't use __init__ because we want to use the context manager pattern.
        Everything that needs an Event Loop MUST be created here.
        """
        try:
            # 1. Connect MCP clients (either via exit stack or manual enter)
            # Here we cascade the aenter calls for clients
            await self.mcp_web_client.__aenter__()
            if self.mcp_mobile_client:
                await self.mcp_mobile_client.__aenter__()

            # 2. Сonfigure status reporter - save event for each step of the workflow
            self.status_reporter = StatusReporter(self.task_id)

            # 3. Initialize the model
            await self._init_gemini_model()

            # 4. Build the graph (safe now because MCPs are connected)
            await self._build_graph()

            return self

        except Exception as e:
            # If initialization failed, guarantee to close resources
            logger.error(f"Failed to initialize CodeGeneratorAgent: {e}")
            raise e

    async def _init_gemini_model(self):
        """
        Initialize Gemini model.
        In the future there will be several node classes (ValidationNodes, RefactoringNodes).
        It is better to create one model instance in the Orchestrator and share it with all nodes,
        rather than having each node create its own connection.
        """
        self.gemini_model = ChatGoogleGenerativeAI(
            model=settings.MODEL_CODEGEN,
            temperature=0.2,
            max_retries=2,
        )

    async def _build_graph(self):
        """
        Builds the Directed Acyclic Graph (DAG) for code generation.
        Includes stages: Validation -> Context -> (Web | Mobile) -> Linters -> Finish.
        """
        # 1. Initialize all nodes with dependencies
        input_nodes = InputValidationNodes(status_reporter=self.status_reporter)

        # Pass both MCP clients
        mcp_nodes = MCPContextRetrievalNode(
            web_client=self.mcp_web_client, mobile_client=self.mcp_mobile_client, status_reporter=self.status_reporter
        )

        # Nodes for Web and Mobile code generation
        web_nodes = WebPipelineNodes(
            self.gemini_model,
            self.status_reporter,
            self.web_workspace,  # Інжектимо workspace
        )

        mobile_nodes = MobilePipelineNodes(
            self.gemini_model,
            self.status_reporter,
            self.mobile_workspace,
        )

        # 2. Create graph with typed state
        workflow = StateGraph(CodeGenState)

        # --- Add Nodes ---

        # Common stages for all flows: web and mobile
        workflow.add_node("validate_input", input_nodes.validate_input)
        workflow.add_node("retrieve_mcp_context", mcp_nodes.retrieve_context)

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

        # Add subgraphs for web and mobile
        # Generic Branch Building
        # Add Web branch
        self._add_pipeline_branch(workflow, nodes=web_nodes, prefix="web", start_node="retrieve_mcp_context")

        # Додаємо Mobile гілку (якщо треба)
        self._add_pipeline_branch(workflow, nodes=mobile_nodes, prefix="mobile", start_node="retrieve_mcp_context")

        # 3. Compile LangGraph workflow graph
        self.graph = workflow.compile()
        logger.info("CodeGen Graph built successfully.")

    def _add_pipeline_branch(self, workflow: StateGraph, nodes, prefix: Literal["web", "mobile"], start_node: str):
        """
        Generic method to build a pipeline branch (Web or Mobile).
        Removes code duplication.
        """
        # Define node names dynamically
        n_prepare = f"prepare_{prefix}"
        n_generate = f"generate_{prefix}"
        n_write = f"write_{prefix}"
        n_lint = f"lint_{prefix}"
        n_fix = f"fix_{prefix}"
        n_push = f"push_{prefix}"

        # Add Nodes
        workflow.add_node(n_prepare, nodes.prepare_repo)
        workflow.add_node(n_generate, nodes.generate_code)
        workflow.add_node(n_write, nodes.write_file)
        workflow.add_node(n_lint, nodes.run_linter)
        workflow.add_node(n_fix, nodes.fix_code)
        workflow.add_node(n_push, nodes.push_code)

        # Add Edges
        # Connect start node to this branch
        workflow.add_edge(start_node, n_prepare)

        # Linear flow
        workflow.add_edge(n_prepare, n_generate)
        workflow.add_edge(n_generate, n_write)
        workflow.add_edge(n_write, n_lint)

        # Loop: Lint -> Fix -> Write
        workflow.add_conditional_edges(
            n_lint,
            nodes.should_continue,
            {
                n_fix: n_fix,  # Fix code
                n_push: n_push,  # Success -> Push
            },
        )
        workflow.add_edge(n_fix, n_write)
        workflow.add_edge(n_push, END)

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

    async def run(self, initial_state: CodeGenState):
        """Method to run the graph without calling graph.invoke outside"""
        if not self.graph:
            raise RuntimeError("CodeGeneratorAgent: Graph not initialized. Make sure you build the graph first.")
        return await self.graph.ainvoke(initial_state)
