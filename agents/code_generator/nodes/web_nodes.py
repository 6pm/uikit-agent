"""Web Pipeline Nodes - handles the full lifecycle of Web Code Generation."""

import json
from datetime import datetime
from typing import Any, Literal

import anyio
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.code_generator.prompts import FIX_LINTER_PROMPT_WEB, FIX_LINTER_PROMPT_WEB_SYSTEM, SYSTEM_PROMPT_WEB, USER_MESSAGE_WEB_START
from agents.code_generator.state import CodeGenState, StatusEvent
from app.services.repository_workspace import RepositoryWorkspace
from app.services.status_reporter import StatusReporter
from app.utils.code import clean_code_output
from app.utils.logger_config import logger

MAX_ITERATIONS = 3


def get_web_file_path(component_name: str) -> str:
    return f"src/app/preview/{component_name}/page.tsx"


class WebPipelineNodes:
    """
    Nodes responsible for the Web Code Generation lifecycle.

    Includes:
    1. Repo preparation (Clone/Checkout)
    2. Code Generation (LLM)
    3. File Writing (IO)
    4. Linting & Fixing (Tooling)
    5. Self-Correction (LLM)
    6. Git Push
    """

    def __init__(self, model: ChatGoogleGenerativeAI, status_reporter: StatusReporter, workspace: RepositoryWorkspace):
        self.model = model
        self.reporter = status_reporter
        # class that works with repository - clone, update files, commit.
        self.workspace = workspace

    # =========================================================================
    # INTERNAL HELPERS
    # =========================================================================

    def _get_component_name(self, state: CodeGenState) -> str:
        """
        Function that returns the component name where our code will be
        """
        task_id_prefix = state["task_id"][:8]
        name = f"{state.get('component_name', 'component')}"

        return f"{name}-{task_id_prefix}"

    # --- NODE 1: Prepare Repository ---
    async def prepare_repo(self, state: CodeGenState) -> dict[str, Any]:
        """Clones repo and creates a feature branch."""
        # branch where we'll push the code
        branch_name = f"codegen/{self._get_component_name(state)}"

        try:
            await self.reporter.report(
                StatusEvent(
                    timestamp=datetime.now().isoformat(),
                    scope="web_git",
                    status="pending",
                    message="Preparing Web Repository",
                    details={"branch": branch_name},
                )
            )

            # Execute heavy IO operation in a separate thread
            await anyio.to_thread.run_sync(self.workspace.prepare_repo, branch_name)

            return {"web_iterations": 0}  # Reset the attempt counter

        except Exception as e:
            logger.error(f"Web Repo Prep Error: {e}", exc_info=True)
            error_msg = StatusEvent(
                timestamp=datetime.now().isoformat(),
                scope="web_git",
                status="error",
                message=f"Repo preparation failed: {str(e)}",
            )
            await self.reporter.report(error_msg)

            # stop the workflow with the error
            raise e
            # return {"status_history": [error_msg], "error": "REPO_PREP_FAILED"}

    # --- NODE 2: Generate Code (LLM) ---
    async def generate_code(self, state: CodeGenState) -> dict[str, Any]:
        """Generates initial React Web Code based on prompts."""

        message = StatusEvent(
            timestamp=datetime.now().isoformat(),
            scope="web_gen",
            status="pending",
            message="Starting Web code generation",
        )
        await self.reporter.report(message)

        # 1. Construct messages
        messages = [
            SystemMessage(content=SYSTEM_PROMPT_WEB),
            HumanMessage(
                content=f"""
                {USER_MESSAGE_WEB_START}

                Additional user prompt for UI generation: {state["user_prompt"]}

                ## @patrianna/uikit context from MCP:
                {state.get("web_docs", "No docs provided")}

                ##Figma Structure:
                {json.dumps(state.get("figma_json", {}))}
            """
            ),
        ]

        try:
            # 2. Invoke the model
            response = await self.model.ainvoke(messages)
            generated_code = clean_code_output(response.content)

            # 3. Report success
            message = StatusEvent(
                timestamp=datetime.now().isoformat(),
                scope="web_gen",
                status="success",
                message="Web code generated - initial phase",
            )
            await self.reporter.report(message)

            return {
                "web_code": generated_code,
                "status_history": [message],
            }

        except Exception as e:
            logger.error("Web Gen Error: %s", e, exc_info=True)
            error_message = StatusEvent(
                timestamp=datetime.now().isoformat(),
                scope="web_gen",
                status="error",
                message=f"Initial code generation failed: {str(e)}",
            )
            await self.reporter.report(error_message)
            return {"status_history": [error_message]}

    # --- NODE 3: Write File ---
    async def write_file(self, state: CodeGenState) -> dict[str, Any]:
        """Writes the generated code to the file system in the workspace."""
        component_name = self._get_component_name(state)
        # File path: src/components/Button/Button.tsx
        file_path = get_web_file_path(component_name)

        try:
            await anyio.to_thread.run_sync(self.workspace.inject_code, file_path, state["web_code"])
            message = StatusEvent(
                timestamp=datetime.now().isoformat(),
                scope="web_write",
                status="success",
                message=f"Web code written to file: '{file_path}'",
            )
            await self.reporter.report(message)

            return {
                "status_history": [message],
            }

        except Exception as e:
            logger.error("Web Write Error: %s", e, exc_info=True)
            error_message = StatusEvent(
                timestamp=datetime.now().isoformat(),
                scope="web_write",
                status="error",
                message=f"Web code writing failed: {str(e)}",
            )
            await self.reporter.report(error_message)

            return {"status_history": [error_message]}

    # --- NODE 4: Linter (The Judge) ---
    async def run_linter(self, state: CodeGenState) -> dict[str, Any]:
        """Runs eslint --fix on the written file."""
        try:
            await self.reporter.report(
                StatusEvent(timestamp=datetime.now().isoformat(), scope="web_lint", status="pending", message="Running Linter")
            )

            # Run linter and fix the code
            success, output = await anyio.to_thread.run_sync(self.workspace.run_linter_fix)

            component_name = self._get_component_name(state)
            file_path = get_web_file_path(component_name)

            if success:
                # Read file back, as linter may have changed formatting
                clean_code = await anyio.to_thread.run_sync(self.workspace.read_file, file_path)

                success_msg = StatusEvent(
                    timestamp=datetime.now().isoformat(), scope="web_lint", status="success", message="Linter passed (auto-fixed)"
                )
                await self.reporter.report(success_msg)

                return {
                    "web_code": clean_code,  # Update code
                    "web_lint_errors": None,  # Clear errors
                    "status_history": [success_msg],
                }

            # If error
            warn_msg = StatusEvent(
                timestamp=datetime.now().isoformat(),
                scope="web_lint",
                status="warning",
                message="Linter found errors",
                details={"errors": output[:500]},  # Обрізаємо лог
            )
            await self.reporter.report(warn_msg)

            return {"web_lint_errors": output, "web_iterations": state.get("web_iterations", 0) + 1, "status_history": [warn_msg]}

        except Exception as e:
            logger.error("Web Lint Error: %s", e, exc_info=True)
            return {"web_lint_errors": str(e)}

    # --- NODE 5: Fix Code (Self-Correction) ---
    async def fix_code(self, state: CodeGenState) -> dict[str, Any]:
        """Asks LLM to fix the code based on linter errors."""
        try:
            await self.reporter.report(
                StatusEvent(
                    timestamp=datetime.now().isoformat(),
                    scope="web_fix",
                    status="pending",
                    message=f"Fixing code (Attempt {state.get('web_iterations')})",
                )
            )

            messages = [
                SystemMessage(content=FIX_LINTER_PROMPT_WEB_SYSTEM),
                HumanMessage(content=FIX_LINTER_PROMPT_WEB(state["web_code"], state["web_lint_errors"])),
            ]

            response = await self.model.ainvoke(messages)
            fixed_code = clean_code_output(response.content)

            return {"web_code": fixed_code}

        except Exception as e:
            logger.error("Web Fix Error: %s", e, exc_info=True)
            return {}  # If it failed, return with the same code and linter will fail again (until limit)

    # --- NODE 6: Push Code ---
    async def push_code(self, state: CodeGenState) -> dict[str, Any]:
        """Commits and pushes the code to the remote repository."""
        component_name = self._get_component_name(state)
        branch_name = f"codegen/{component_name}"
        msg = f"feat({component_name}): generate component via Agent"
        if state.get("web_lint_errors"):
            msg += " (forced push with linter errors)"

        try:
            await anyio.to_thread.run_sync(self.workspace.commit_and_push, msg, branch_name)

            success_msg = StatusEvent(
                timestamp=datetime.now().isoformat(),
                scope="web_git",
                status="success",
                message=f"Code pushed to branch: '{branch_name}'",
            )
            await self.reporter.report(success_msg)
            return {"status_history": [success_msg]}

        except Exception as e:
            logger.error("Web Push Error: %s", e, exc_info=True)
            error_msg = StatusEvent(timestamp=datetime.now().isoformat(), scope="web_git", status="error", message=f"Git push failed: {str(e)}")
            await self.reporter.report(error_msg)
            return {"status_history": [error_msg]}

    # --- ROUTER ---
    def should_continue(self, state: CodeGenState) -> Literal["fix_web", "push_web"]:
        errors = state.get("web_lint_errors")
        iterations = state.get("web_iterations", 0)

        # If there are errors and less than 3 attempts -> Fix
        if errors and iterations < MAX_ITERATIONS:
            return "fix_web"

        # Otherwise (success or limit) -> Push
        return "push_web"
