"""
Huey task TODO

B
"""
import logging
import time
# from typing import Dict, Any
from config import huey
# from agents.code_generator import CodeGeneratorAgent

logger = logging.getLogger(__name__)

@huey.task()
def generate_code_from_figma(json: str):
    """
BEST PRACTICES:
1. Keep tasks thin - delegate to agent class
2. Handle serialization properly (JSON-serializable data only)
3. Log everything for debugging
4. Return structured results
    """
    # Use logger.info instead of print

    time.sleep(5) # Simulate 5 seconds of work

    result = "generate_code_from_figma: RESULT AAAA"

    #  Log our result!
    logger.info("[HUEY WORKER]: Task generate_code_from_figma completed! Result: %s", result)

    return result


# @huey.task()
# def generate_code_from_figma(request_data: Dict[str, Any]) -> Dict[str, Any]:
#     """
#     Background task for generating code from Figma components.

#     BEST PRACTICE: Task should be a thin wrapper around business logic.
#     This allows:
#     - Easy testing (test agent separately)
#     - Reuse (agent can be called directly if needed)
#     - Clear separation of concerns

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
