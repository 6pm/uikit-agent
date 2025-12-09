"""Web Generator Node - generates React Web code."""

import asyncio
import json
from datetime import datetime
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.code_generator.prompts import SYSTEM_PROMPT_WEB, USER_MESSAGE_WEB_START
from agents.code_generator.state import CodeGenState
from app.utils.code import clean_code_output
from app.utils.logger_config import logger


# Web Generator Logic
class WebCodeGenNode:
    """
    Node responsible for generating React Web code.

    This node encapsulates the logic for interacting with the AI model:
    sending prompts, parsing responses, and handling errors.
    It follows the Dependency Injection principle by receiving the model instance.
    """

    def __init__(self, model: ChatGoogleGenerativeAI):
        """
        Initialize the WebCodeGenNode.

        Args:
            model (ChatGoogleGenerativeAI): The language model instance used for code generation.
        """
        self.model = model

    async def generate_code(self, state: CodeGenState) -> dict[str, Any]:
        """
        Generate React Web Code based on the current state.

        This method operates in an isolated context, constructing its own
        messages rather than relying on global state messages.

        Args:
            state (CodeGenState): The current state containing user prompt, Figma JSON, and docs.

        Returns:
            dict[str, Any]: A dictionary containing the generated 'web_code' and status history update.
        """

        # 1. Construct messages LOCALLY for this node
        messages = [
            SystemMessage(content=SYSTEM_PROMPT_WEB),
            HumanMessage(
                content=f"""
                {USER_MESSAGE_WEB_START}

                Additional user prompt for UI generation: {state["user_prompt"]}

                ## @patrianna/uikit context from MCP:
                {state["web_docs"]}

                ##Figma Structure:
                {json.dumps(state["figma_json"])}
            """
            ),
        ]

        try:
            # 2. Invoke the model
            response = await self.model.ainvoke(messages)
            generated_code = clean_code_output(response.content)

            # 3. Return the result in the isolated 'web_code' field
            return {
                "web_code": generated_code,
                "status_history": [
                    {
                        "timestamp": datetime.now().isoformat(),
                        "scope": "web",
                        "status": "success",
                        "message": "Web code generated",
                        "details": None,
                    }
                ],
            }
        except Exception as e:
            logger.error("Web Gen Error: %s", e, exc_info=True)
            return {
                "status_history": [
                    {
                        "timestamp": datetime.now().isoformat(),
                        "scope": "web",
                        "status": "error",
                        "message": f"Generation failed: {str(e)}",
                        "details": None,
                    }
                ]
            }

    async def run_linter(self, state: CodeGenState) -> dict[str, Any]:
        """
        Run linter (ESLint) on the generated web code.

        Currently serves as a placeholder simulating a linter run.

        Args:
            state (CodeGenState): The current state containing generated code.

        Returns:
            dict[str, Any]: A dictionary containing the linter results in 'status_history'.
        """
        # Placeholder for ESLint execution logic via subprocess
        logger.info("Running fake linter for 1 second...")
        await asyncio.sleep(1)

        return {
            "status_history": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "scope": "web",
                    "status": "success",
                    "message": "Linting passed (fake) - delay 1 second",
                    "details": None,
                }
            ]
        }
