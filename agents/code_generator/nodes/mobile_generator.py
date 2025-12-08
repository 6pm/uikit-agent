"""Mobile Generator Node - generates React Native code."""

import asyncio
import json
from datetime import datetime
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.code_generator.prompts import SYSTEM_PROMPT_MOBILE, USER_MESSAGE_MOBILE_START
from agents.code_generator.state import CodeGenState
from src.logger_config import logger


class MobileCodeGenNode:
    """
    Node responsible for generating React Native (Mobile) code.

    This node takes the parsed Figma JSON and user prompt from the state,
    combines them with mobile-specific documentation context, and prompts
    the LLM to generate the corresponding React Native component code.
    """

    def __init__(self, model: ChatGoogleGenerativeAI):
        """
        Initialize the MobileCodeGenNode.

        Args:
            model (ChatGoogleGenerativeAI): The language model instance used for code generation.
        """
        self.model = model

    async def generate_code(self, state: CodeGenState) -> dict[str, Any]:
        """
        Generate React Native code based on the current state.

        Constructs the prompt using the system prompt, user prompt, retrieved
        mobile docs, and Figma JSON structure.

        Args:
            state (CodeGenState): The current state of the generation workflow.

        Returns:
            dict[str, Any]: A dictionary containing the generated 'mobile_code'
            and an update to the 'status_history'.
        """
        messages = [
            SystemMessage(content=SYSTEM_PROMPT_MOBILE),
            HumanMessage(
                content=f"""
                {USER_MESSAGE_MOBILE_START}

                Additional user prompt for UI generation: {state["user_prompt"]}

                Context: {state["mobile_docs"]}

                ##Figma Structure:
                {json.dumps(state["figma_json"])}
            """
            ),
        ]

        response = await self.model.ainvoke(messages)

        return {
            "mobile_code": response.content,
            "status_history": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "scope": "mobile",
                    "status": "success",
                    "message": "Mobile code generated",
                    "details": None,
                }
            ],
        }

    async def run_linter(self, state: CodeGenState) -> dict[str, Any]:
        """
        Run linter (ESLint) on the generated mobile code.

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
                    "scope": "mobile",
                    "status": "success",
                    "message": "Linting mobile code passed (fake) - delay 1 second",
                    "details": None,
                }
            ]
        }
