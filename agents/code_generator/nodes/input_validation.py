from datetime import datetime
from typing import Any, Literal

from langgraph.graph import END

from agents.code_generator.state import CodeGenState
from src.logger_config import logger


class InputValidationNodes:
    """
    Common node for validating input data, specifically Figma JSON and User Prompt.

    This class handles the initial validation step in the LangGraph workflow,
    ensuring that the necessary data is present before proceeding to context retrieval
    and code generation.
    """

    async def validate_input(self, state: CodeGenState) -> dict[str, Any]:
        """
        Validates the input state to ensure required data is present.

        Checks if 'figma_json' exists in the state. If missing, records an error
        in the status history.

        Args:
            state (CodeGenState): The current state of the execution graph.

        Returns:
            dict[str, Any]: Updates to the state, specifically appending to 'status_history'.
        """
        figma_data = state.get("figma_json")

        if not figma_data:
            return {
                "status_history": [
                    {
                        "timestamp": datetime.now().isoformat(),
                        "status": "error",
                        "scope": "common",
                        "message": "Missing Figma Data",
                        "details": None,
                    }
                ]
            }

        return {
            "status_history": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "status": "success",
                    "scope": "common",
                    "message": "Input validated successfully",
                    "details": None,
                }
            ]
        }

    def should_continue(self, state: CodeGenState) -> Literal["retrieve_mcp_context", END]:
        """
        Router function for LangGraph conditional edges.

        Determines the next step in the graph based on the result of the input validation.
        If validation failed, the workflow stops (END). Otherwise, it proceeds to MCP context retrieval.

        Args:
            state (CodeGenState): The current state of the execution graph.

        Returns:
            Literal["retrieve_mcp_context", END]: The next node to execute or END to stop.
        """
        # Check if there is an error in the state by inspecting the last status message in status_history
        last_status = state["status_history"][-1]["status"]

        if last_status == "error":
            logger.warning("Validation failed: %s. Stopping execution.", last_status)
            return END

        return "retrieve_mcp_context"
