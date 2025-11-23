"""
Task for generating code
"""

import asyncio
import logging

from agents.code_generator_agent import CodeGeneratorAgent
from config import huey
from schemas.ai_models.test_ai_response import TestAIResponse
from schemas.api.code_generation_types import CodeGenerationRequest

logger = logging.getLogger(__name__)


@huey.task()
def code_generation_task(request_data: dict):
    """
    BEST PRACTICES:
    - Handle serialization properly (JSON-serializable data only)
    - Return structured results
    - Always use try-catch for error handling
    """
    logger.info("[HUEY WORKER]: Starting code generation task")

    # Re-hydration: Відновлюємо типізовану модель
    try:
        request_data_typed = CodeGenerationRequest(**request_data)
    except Exception as e:
        print(f"Re-hydration code_generation_task: Critical data error: {e}")
        return  # Або логуємо і виходимо, бо дані биті

    try:
        # Huey tasks must be synchronous, but we can run async code inside
        return asyncio.run(_async_code_generation(request_data_typed))

    except Exception as e:
        error_msg = f"Code generation task failed: {str(e)}"
        logger.error("[HUEY WORKER]: %s", error_msg, exc_info=True)

        # BEST PRACTICE: Always return structured error response
        return {"success": False, "errors": [error_msg], "generated_code": None}


async def _async_code_generation(request_data: CodeGenerationRequest) -> TestAIResponse:
    """
    Async implementation of code generation.
    This is called from the sync Huey task using uvloop.run().
    """
    logger.info("[HUEY WORKER]: Starting _async_code_generation fnc")
    logger.debug("[HUEY WORKER]: Request data: %s", request_data)

    try:
        agent = await CodeGeneratorAgent.create()

        # print("request_data GGGGGGGGGGGGGGGGGGG", request_data)
        result = await agent.generate_code(request_data)
        # result = {"messages": [{"role": "ai", "content": "hello world and AAAAAAAAAA"}]}

        # Log our result!
        logger.info("[HUEY WORKER]: Task generate_code_from_figma completed! Result: %s", result)

        return result

    except Exception as e:
        error_msg = f"Code generation task failed: {str(e)}"
        logger.error("[HUEY WORKER]: %s", error_msg, exc_info=True)
        return {"success": False, "errors": [error_msg], "generated_code": None}


# @huey.task()
# def generate_code_from_figma(request_data: Dict[str, Any]) -> Dict[str, Any]:
#     """
#     Background task for generating code from Figma components.

#     Args:
#         request_data: Dictionary containing:
#             - figma_components: List of component dicts
#             - target_framework: Framework name (default: "react")
#             - output_format: Output format (default: "tsx")
#             - style_approach: Styling approach (default: "tailwind")

#     Returns:
#         Dictionary with generation results
#     """
#     logger.info("[HUEY WORKER]: Starting code generation task")
#     logger.debug(f"[HUEY WORKER]: Request data: {request_data}")

#     try:
#         # BEST PRACTICE: Initialize agent inside task (not globally)
#         # This ensures fresh state and proper error isolation
#         agent = CodeGeneratorAgent(model_provider="openai")

#         # Execute generation
#         result = agent.generate(request_data)

#         logger.info(f"[HUEY WORKER]: Task completed. Success: {result.get('success', False)}")

#         if result.get("errors"):
#             logger.warning(f"[HUEY WORKER]: Errors encountered: {result['errors']}")

#         return result

#     except Exception as e:
#         error_msg = f"Code generation task failed: {str(e)}"
#         logger.error(f"[HUEY WORKER]: {error_msg}", exc_info=True)

#         # BEST PRACTICE: Always return structured error response
#         return {
#             "success": False,
#             "errors": [error_msg],
#             "generated_code": None
#         }
