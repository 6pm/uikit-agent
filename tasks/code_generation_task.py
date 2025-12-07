"""
Task for generating code
"""

import asyncio

from agents.code_generator import CodeGeneratorAgent
from agents.code_generator.state import CodeGenState
from config import huey
from schemas.ai_models.test_ai_response import TestAIResponse
from schemas.api.code_generation_types import CodeGenerationRequest
from src.logger_config import logger


@huey.task()
def code_generation_task(request_data: dict):
    """
    BEST PRACTICES:
    - Handle serialization properly (JSON-serializable data only)
    - Return structured results
    - Always use try-catch for error handling
    """
    logger.info("code_generation_task: Starting code generation task")

    # Re-hydration: restore pydantic types from dict
    try:
        request_data_typed = CodeGenerationRequest(**request_data)
    except Exception as e:
        logger.info("code_generation_task: Re-hydration critical data error: %s", e, exc_info=True)
        return  # error and exit

    try:
        # Huey tasks must be synchronous, but we can run async code inside
        return asyncio.run(_async_code_generation(request_data_typed))

    except Exception as e:
        error_msg = "code_generation_task: Code generation task failed: %s", e
        logger.error("code_generation_task: %s", error_msg, exc_info=True)

        # BEST PRACTICE: Always return structured error response
        return {"success": False, "errors": [error_msg], "generated_code": None}


async def _async_code_generation(request_data: CodeGenerationRequest) -> TestAIResponse:
    """
    Async implementation of code generation.
    This is called from the sync Huey task using uvloop.run().
    """
    logger.info("code_generation_task: Initializing agent for task ...")
    logger.debug("code_generation_task: Request data: %s", request_data)

    try:
        # 1. Створення агента (тут відбудеться connect до MCP та build_graph)
        agent = await CodeGeneratorAgent.create()

        # 2. Підготовка початкового стану
        initial_state: CodeGenState = {
            "figma_json": request_data.figmaJson,
            "user_prompt": request_data.userPrompt,
            "component_name": request_data.componentName,
            "status_history": [],
            "web_docs": None,
            "mobile_docs": None,
            "web_code": None,
            "mobile_code": None,
        }

        # 3. ЗАПУСК ГРАФА
        # Це найважча операція, яка займе 30-60+ секунд
        logger.info("Invoking graph for task...")
        final_state: CodeGenState = await agent.graph.ainvoke(initial_state)

        # 4. Обробка результатів
        logger.info("code_generation_task: Task completed.")

        return final_state

    except Exception as e:
        logger.error("Error inside agent execution: %s", e, exc_info=True)
        return {"error": str(e)}

    finally:
        # 5. Очистка ресурсів (Закриваємо MCP з'єднання)
        if agent:
            await agent.close()
            logger.info("code_generation_task: Agent resources closed.")
