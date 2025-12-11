import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import anyio
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.code_generator.state import CodeGenState, StatusEvent
from app.services.repository_workspace import RepositoryWorkspace
from app.services.status_reporter import StatusReporter
from app.utils.code import clean_code_output
from app.utils.logger_config import logger

MAX_ITERATIONS = 3


class BaseCodeGenNodes(ABC):
    """
    Abstract base class for code generation pipelines (Web & Mobile).
    Implements the Template Method pattern.
    """

    # Define the platform prefix ('web' or 'mobile') to generate state keys dynamically
    platform: str = ""

    def __init__(self, model: ChatGoogleGenerativeAI, status_reporter: StatusReporter, workspace: RepositoryWorkspace):
        self.model = model
        self.reporter = status_reporter
        self.workspace = workspace

    # =========================================================================
    # ABSTRACT METHODS (To be implemented by Web/Mobile classes)
    # =========================================================================

    @abstractmethod
    def _get_file_path(self, component_name: str) -> str:
        """Returns the target file path for the generated code."""
        pass

    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Returns the initial generation system prompt."""
        pass

    @abstractmethod
    def _get_user_prompt_start(self) -> str:
        """Returns the start of the user prompt."""
        pass

    @abstractmethod
    def _get_fix_prompts(self) -> tuple[str, Any]:
        """Returns (System Prompt, Function to generate User Prompt) for fixing."""
        pass

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _get_component_name(self, state: CodeGenState) -> str:
        task_id_prefix = state["task_id"][:8]
        name = f"{state.get('component_name', 'component')}"
        return f"{name}-{task_id_prefix}"

    def _key(self, suffix: str) -> str:
        """Helper to generate keys like 'web_code', 'mobile_git', etc."""
        return f"{self.platform}_{suffix}"

    # =========================================================================
    # PIPELINE NODES (Generic Logic)
    # =========================================================================

    # --- NODE 1: Prepare Repository ---
    async def prepare_repo(self, state: CodeGenState) -> dict[str, Any]:
        branch_name = f"codegen/{self._get_component_name(state)}"
        scope = self._key("git")  # web_git / mobile_git

        try:
            await self.reporter.report(
                StatusEvent(
                    timestamp=datetime.now().isoformat(),
                    scope=scope,
                    status="pending",
                    message=f"Preparing {self.platform.capitalize()} Repository",
                    details={"branch": branch_name},
                )
            )

            await anyio.to_thread.run_sync(self.workspace.prepare_repo, branch_name)

            await self.reporter.report(
                StatusEvent(
                    timestamp=datetime.now().isoformat(), scope=scope, status="success", message=f"{self.platform.capitalize()} Repository prepared"
                )
            )

            # Return like {"web_iterations": 0}
            return {self._key("iterations"): 0}

        except Exception as e:
            logger.error(f"{self.platform.capitalize()} Repo Prep Error: {e}", exc_info=True)
            await self.reporter.report(
                StatusEvent(
                    timestamp=datetime.now().isoformat(),
                    scope=scope,
                    status="error",
                    message=f"{self.platform.capitalize()} repository preparation failed: {str(e)}",
                )
            )
            raise e

    # --- NODE 2: Generate Code ---
    async def generate_code(self, state: CodeGenState) -> dict[str, Any]:
        scope = self._key("gen")

        await self.reporter.report(
            StatusEvent(
                timestamp=datetime.now().isoformat(), scope=scope, status="pending", message=f"Starting {self.platform.capitalize()} code generation"
            )
        )

        # Dynamic retrieval of docs: state["web_docs"] or state["mobile_docs"]
        docs_key = self._key("docs")
        docs = state.get(docs_key, "No docs provided")

        messages = [
            SystemMessage(content=self._get_system_prompt()),
            HumanMessage(
                content=f"""
                {self._get_user_prompt_start()}
                Additional user prompt: {state["user_prompt"]}
                ## Context:
                {docs}
                ## Figma Structure:
                {json.dumps(state.get("figma_json", {}))}
            """
            ),
        ]

        try:
            response = await self.model.ainvoke(messages)
            generated_code = clean_code_output(response.content)

            msg = StatusEvent(
                timestamp=datetime.now().isoformat(),
                scope=scope,
                status="success",
                message=f"{self.platform.capitalize()} Code generated - initial phase",
            )
            await self.reporter.report(msg)

            # Return {"web_code": ...}
            return {
                self._key("code"): generated_code,
                "status_history": [msg],
            }

        except Exception as e:
            logger.error(f"{self.platform} Gen Error: {e}", exc_info=True)
            error_msg = StatusEvent(
                timestamp=datetime.now().isoformat(),
                scope=scope,
                status="error",
                message=f"{self.platform.capitalize()} code generation failed: {str(e)}",
            )
            await self.reporter.report(error_msg)
            return {"status_history": [error_msg]}

    # --- NODE 2.5: Generate Fake Code (for testing) ---
    async def generate_code_fake(self, state: CodeGenState) -> dict[str, Any]:
        """
        Generates fake code data for testing purposes.
        Returns different code for web and mobile platforms.
        """
        scope = self._key("gen")

        await self.reporter.report(
            StatusEvent(
                timestamp=datetime.now().isoformat(),
                scope=scope,
                status="pending",
                message=f"Generating fake {self.platform.capitalize()} code",
            )
        )

        # Generate platform-specific fake code
        if self.platform == "web":
            fake_code = """"use client"

import { Button } from "@patrianna/uikit/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@patrianna/uikit/card"

export default function FakeComponent() {
  return (
    <div className="container mx-auto p-4">
<Card>
<CardHeader>
<CardTitle>Fake title</CardTitle>
<CardDescription>Generated fake web component 222</CardDescription>
</CardHeader>
<CardContent>
<Button>Click me</Button>
</CardContent>
</Card>
    </div>
  )
}"""
        else:  # mobile
            fake_code = """import React from "react"
import { View, Text, TouchableOpacity, StyleSheet } from "react-native"

export default function FakeComponent() {
  return (
    <View style={styles.container}>
<Text style={styles.title}>Fake title</Text>
<Text style={styles.description}>Generated fake mobile component 222</Text>
<TouchableOpacity style={styles.button}>
<Text style={styles.buttonText}>Press me</Text>
      </TouchableOpacity>
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    backgroundColor: "#fff",
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    marginBottom: 8,
  },
  description: {
    fontSize: 14,
    color: "#666",
    marginBottom: 16,
  },
  button: {
    backgroundColor: "#007AFF",
    padding: 12,
    borderRadius: 8,
    alignItems: "center",
  },
  buttonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
})
"""

        msg = StatusEvent(
            timestamp=datetime.now().isoformat(),
            scope=scope,
            status="success",
            message=f"Fake {self.platform.capitalize()} code generated",
        )
        await self.reporter.report(msg)

        return {
            self._key("code"): fake_code,
            "status_history": [msg],
        }

    # --- NODE 3: Write File ---
    async def write_file(self, state: CodeGenState) -> dict[str, Any]:
        component_name = self._get_component_name(state)
        file_path = self._get_file_path(component_name)
        scope = self._key("write")

        # Get code dynamically: state["web_code"]
        code = state.get(self._key("code"))

        try:
            await anyio.to_thread.run_sync(self.workspace.inject_code, file_path, code)

            msg = StatusEvent(
                timestamp=datetime.now().isoformat(),
                scope=scope,
                status="success",
                message=f"{self.platform.capitalize()} code written to: '{file_path}'",
            )
            await self.reporter.report(msg)
            return {"status_history": [msg]}

        except Exception as e:
            logger.error(f"{self.platform} Write Error: {e}", exc_info=True)
            error_msg = StatusEvent(
                timestamp=datetime.now().isoformat(), scope=scope, status="error", message=f"{self.platform.capitalize()} writing failed: {str(e)}"
            )
            await self.reporter.report(error_msg)
            return {"status_history": [error_msg]}

    # --- NODE 4: Linter ---
    async def run_linter(self, state: CodeGenState) -> dict[str, Any]:
        scope = self._key("lint")
        try:
            await self.reporter.report(
                StatusEvent(
                    timestamp=datetime.now().isoformat(), scope=scope, status="pending", message=f"{self.platform.capitalize()} running Linter"
                )
            )

            success, output = await anyio.to_thread.run_sync(self.workspace.run_linter_fix)

            component_name = self._get_component_name(state)
            file_path = self._get_file_path(component_name)

            if success:
                clean_code = await anyio.to_thread.run_sync(self.workspace.read_file, file_path)
                success_msg = StatusEvent(
                    timestamp=datetime.now().isoformat(),
                    scope=scope,
                    status="success",
                    message=f"{self.platform.capitalize()} Linter passed (auto-fixed)",
                )
                await self.reporter.report(success_msg)

                return {
                    self._key("code"): clean_code,
                    self._key("lint_errors"): None,
                    "status_history": [success_msg],
                }

            # Errors found
            warn_msg = StatusEvent(
                timestamp=datetime.now().isoformat(),
                scope=scope,
                status="warning",
                message=f"{self.platform.capitalize()} linter found errors",
                details={"errors": output[:500]},
            )
            await self.reporter.report(warn_msg)

            iter_key = self._key("iterations")
            return {self._key("lint_errors"): output, iter_key: state.get(iter_key, 0) + 1, "status_history": [warn_msg]}

        except Exception as e:
            logger.error(f"{self.platform} Lint Error: {e}", exc_info=True)
            return {self._key("lint_errors"): str(e)}

    # --- NODE 5: Fix Code ---
    async def fix_code(self, state: CodeGenState) -> dict[str, Any]:
        scope = self._key("fix")
        iter_key = self._key("iterations")

        try:
            await self.reporter.report(
                StatusEvent(
                    timestamp=datetime.now().isoformat(),
                    scope=scope,
                    status="pending",
                    message=f"{self.platform.capitalize()} fixing code (Attempt {state.get(iter_key)})",
                )
            )

            system_prompt, user_prompt_func = self._get_fix_prompts()

            current_code = state[self._key("code")]
            errors = state[self._key("lint_errors")]

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt_func(current_code, errors)),
            ]

            response = await self.model.ainvoke(messages)
            fixed_code = clean_code_output(response.content)

            return {self._key("code"): fixed_code}

        except Exception as e:
            logger.error(f"{self.platform} Fix Error: {e}", exc_info=True)
            return {}

    # --- NODE 6: Push Code ---
    async def push_code(self, state: CodeGenState) -> dict[str, Any]:
        component_name = self._get_component_name(state)
        branch_name = f"codegen/{component_name}"
        scope = self._key("git")

        msg = f"feat({component_name}): generate {self.platform} component"
        if state.get(self._key("lint_errors")):
            msg += " (forced push with errors)"

        try:
            await anyio.to_thread.run_sync(self.workspace.commit_and_push, msg, branch_name)
            success_msg = StatusEvent(timestamp=datetime.now().isoformat(), scope=scope, status="success", message=f"Pushed to '{branch_name}'")
            await self.reporter.report(success_msg)
            return {"status_history": [success_msg]}

        except Exception as e:
            logger.error(f"{self.platform} Push Error: {e}", exc_info=True)
            error_msg = StatusEvent(
                timestamp=datetime.now().isoformat(), scope=scope, status="error", message=f"{self.platform.capitalize()} Git push failed: {str(e)}"
            )
            await self.reporter.report(error_msg)
            return {"status_history": [error_msg]}

    # --- ROUTER ---
    def should_continue(self, state: CodeGenState) -> str:
        errors = state.get(self._key("lint_errors"))
        iterations = state.get(self._key("iterations"), 0)

        # Returns "fix_web" or "fix_mobile"
        if errors and iterations < MAX_ITERATIONS:
            return f"fix_{self.platform}"

        # Returns "push_web" or "push_mobile"
        return f"push_{self.platform}"
