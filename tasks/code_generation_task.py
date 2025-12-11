"""
This module contains the Huey task definition for code generation.
It handles the asynchronous execution of the code generation workflow
triggered by the API, managing the bridge between synchronous Huey tasks
and the asynchronous LangGraph agent.
"""

import anyio

from agents.code_generator.agent import CodeGeneratorAgent
from agents.code_generator.state import CodeGenState
from app.utils.logger_config import logger
from config import huey
from schemas.api.code_generation_types import CodeGenerationRequest, CodeGenTaskResult


@huey.task(context=True)
def code_generation_task(request_data: dict, task=None):
    """
    Huey task wrapper for code generation.

    This function acts as a synchronous entry point for the background worker.
    It deserializes the request data, initializes the async loop, and executes
    the agent workflow.

    Args:
        request_data (dict): The raw JSON dictionary from the API request,
                             expected to match CodeGenerationRequest schema.
    """
    logger.info("code_generation_task: Starting code generation task")

    # Re-hydration: restore pydantic types from dict
    try:
        request_data_typed = CodeGenerationRequest(**request_data)
    except Exception as e:
        logger.error("code_generation_task: Re-hydration critical data error: %s", e, exc_info=True)
        return {"success": False, "errors": [f"Re-hydration validation error: {str(e)}"]}

    try:
        # Huey tasks must be synchronous, but we can run async code inside
        return anyio.run(_async_code_generation, request_data_typed, task.id)

    except Exception as e:
        error_msg = f"code_generation_task: Code generation task failed: {e}"
        logger.error("code_generation_task: %s", error_msg, exc_info=True)

        # BEST PRACTICE: Always return structured error response
        return {"success": False, "errors": [error_msg]}


async def _async_code_generation(request_data: CodeGenerationRequest, task_id: str) -> CodeGenTaskResult:
    """
    Asynchronous implementation of the code generation logic.

    This function initializes the CodeGeneratorAgent context manager (which handles
    MCP server lifecycles) and invokes the LangGraph workflow.

    Args:
        request_data (CodeGenerationRequest): The validated request object.
    """
    logger.info("code_generation_task: Initializing agent for task ...")
    logger.debug("code_generation_task: Request data: %s", request_data)

    try:
        # USING ASYNC WITH (Context Manager)
        # This creates a scope where MCP subprocesses and connections live.
        # As soon as the code exits this block (successfully or with an error),
        # cleanup (closing connections, terminating processes) will automatically
        # trigger in the correct order.
        async with CodeGeneratorAgent(task_id) as agent:
            initial_state: CodeGenState = {
                "task_id": task_id,
                "figma_json": request_data.figmaJson,
                "user_prompt": request_data.userPrompt,
                "component_name": request_data.componentName,
                "status_history": [],
                # MCP context
                "web_docs": None,
                "mobile_docs": None,
                # generated code
                "web_code": None,
                "mobile_code": None,
                # linting
                "web_lint_errors": None,
                "web_iterations": 0,
                "mobile_lint_errors": None,
                "mobile_iterations": 0,
            }

            logger.info("Invoking graph for task...")

            # Run the LangGraph workflow
            final_state = await agent.graph.ainvoke(initial_state)

            logger.info("code_generation_task: Task completed.")

            return {
                "status_history": final_state.get("status_history", []),
                "web_code": final_state.get("web_code"),
                "mobile_code": final_state.get("mobile_code"),
                "web_lint_errors": final_state.get("web_lint_errors"),
                "mobile_lint_errors": final_state.get("mobile_lint_errors"),
            }

    except Exception as e:
        logger.error("Error inside agent execution: %s", e, exc_info=True)
        return {"error": str(e)}
