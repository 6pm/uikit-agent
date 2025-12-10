"""Code Generator Agent - orchestrates the code generation workflow."""

from huey.utils import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph

from agents.code_generator.mcp_client import MCPClient
from agents.code_generator.nodes.input_validation import InputValidationNodes
from agents.code_generator.nodes.mcp_context_retrieval import MCPContextRetrievalNode
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
        self.mcp_mobile_client = None

        # configure status reporter - save event for each step of the workflow
        self.status_reporter = StatusReporter(task_id)

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

        # mobile_nodes = MobilePipelineNodes(
        #     self.gemini_model,
        #     self.status_reporter,
        #     self.mobile_workspace,
        # )

        # 2. Create graph with typed state
        workflow = StateGraph(CodeGenState)

        # --- Add Nodes ---

        # Common stages for all flows: web and mobile
        workflow.add_node("validate_input", input_nodes.validate_input)
        workflow.add_node("retrieve_mcp_context", mcp_nodes.retrieve_context)

        # --- WEB BRANCH NODES ---
        workflow.add_node("prepare_web", web_nodes.prepare_repo)
        workflow.add_node("generate_web", web_nodes.generate_code)
        workflow.add_node("write_web", web_nodes.write_file)
        workflow.add_node("lint_web", web_nodes.run_linter)
        workflow.add_node("fix_web", web_nodes.fix_code)
        workflow.add_node("push_web", web_nodes.push_code)

        # # Mobile Branch
        # workflow.add_node("generate_mobile", mobile_codegen_node.generate_code)
        # workflow.add_node("lint_mobile", mobile_codegen_node.run_linter)

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
        workflow.add_edge("retrieve_mcp_context", "prepare_web")
        # workflow.add_edge("retrieve_mcp_context", "prepare_mobile")

        # Linear Flow: Prepare -> Generate -> Write -> Lint
        workflow.add_edge("prepare_web", "generate_web")
        workflow.add_edge("generate_web", "write_web")
        workflow.add_edge("write_web", "lint_web")

        # LOOP: Lint -> (Check) -> Fix -> Write -> Lint
        workflow.add_conditional_edges(
            "lint_web",
            web_nodes.should_continue,  # Router function
            {
                "fix_web": "fix_web",  # go to fix code
                "push_web": "push_web",  # go to push code when no errors or max iterations reached
            },
        )

        # Closing the loop: After Fix -> Write again (to disk) -> Lint again
        workflow.add_edge("fix_web", "write_web")

        # Finish: Push code and end the workflow
        workflow.add_edge("push_web", END)

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
