# from datetime import datetime
# from typing import Any
# import json
# from langchain_core.messages import SystemMessage, HumanMessage
# from langchain_google_genai import ChatGoogleGenerativeAI
# from src.logger_config import logger
# from agents.code_generator.state import CodeGenState
# from agents.code_generator.prompts import SYSTEM_PROMPT_WEB

# # --- 3. Web Generator Logic ---

# # class CodeGenNodes:
# #     """
# #     Знає ЩО робити з моделлю (відправити промпт, розпарсити відповідь).
# #     Він просто отримує інструмент і працює ним.
# #     Тут використовується Dependency Injection принцип.
# #     """
# #
# #     def __init__(self, model):
# #         self.model = model
# #
# #     async def call_model(self, state: CodeGenState) -> dict[str, Any]:
# #         """
# #         Invokes the Gemini model with the current state messages.
# #         """
# #         messages = state["messages"]
# #
# #         logger.info("code_generator.nodes: 🤖 Calling Gemini model...")
# #         response = await self.model.ainvoke(messages)
# #
# #         # LangGraph automatically appends this message to history
# #         # We also update the status
# #         return {"messages": [response], "status": "completed"}
# #
# # async def generate_web_code(self, request_data: CodeGenerationRequest) -> dict[str, Any]:
# #         """
# #         Generate code from Figma JSON data using LangGraph.
# #         This is main function for launching the agent.
# #         As a result it will return generated code and status of the task.
# #
# #         Returns:
# #             dict[str, Any]: Dictionary with generated code and status of the task
# #         """
# #
# #         try:
# #             # Initialization of messages, system prompt and status
# #             inputs = {
# #                 "messages": [
# #                     SystemMessage(content=SYSTEM_PROMPT_WEB),
# #                     HumanMessage(
# #                         content=f"""
# #                         {request_data.userPrompt or ""} \n {USER_MESSAGE_WEB_START} \n
# #                         {json.dumps(request_data.figmaJson, indent=2)}"""
# #                     ),
# #                 ]
# #             }
# #
# #
# # class WebGenNodes:
# #     def __init__(self, model: ChatGoogleGenerativeAI):
# #         self.model = model
# #
# #     async def generate_code(self, state: CodeGenState) -> dict[str, Any]:
# #         """Generates React Web Code. Isolated context."""
# #
# #         # 1. Формуємо повідомлення ЛОКАЛЬНО для цієї ноди
# #         # Ми НЕ беремо сміття з глобального state["messages"], якщо воно там є
# #         messages = [
# #             SystemMessage(content=SYSTEM_PROMPT_WEB),
# #             HumanMessage(
# #                 content=f"""
# #                 User Request: {state["user_prompt"]}
# #
# #                 Docs Context:
# #                 {state["web_docs"]}
# #
# #                 Figma Structure:
# #                 {json.dumps(state["figma_json"])}
# #             """
# #             ),
# #         ]
# #
# #         try:
# #             # 2. Виклик моделі
# #             response = await self.model.ainvoke(messages)
# #             generated_code = response.content
# #
# #             # 3. Повертаємо результат в ізольоване поле web_code
# #             return {
# #                 "web_code": generated_code,
# #                 "status_history": [
# #                     {
# #                         "timestamp": datetime.now().isoformat(),
# #                         "scope": "web",
# #                         "status": "success",
# #                         "message": "Web code generated",
# #                         "details": None,
# #                     }
# #                 ],
# #             }
# #         except Exception as e:
# #             logger.error(f"Web Gen Error: {e}")
# #             return {
# #                 "status_history": [
# #                     {
# #                         "timestamp": datetime.now().isoformat(),
# #                         "scope": "web",
# #                         "status": "error",
# #                         "message": f"Generation failed: {str(e)}",
# #                         "details": None,
# #                     }
# #                 ]
# #             }
# #
# #     async def run_linter(self, state: CodeGenState) -> dict[str, Any]:
# #         # Тут буде логіка запуску ESLint через subprocess
# #         # ...
# #         return {"status_history": [...]}
