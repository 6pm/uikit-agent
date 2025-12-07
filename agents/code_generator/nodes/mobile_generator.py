# from datetime import datetime
# from typing import Any
# import json
# from langchain_core.messages import SystemMessage, HumanMessage
# from langchain_google_genai import ChatGoogleGenerativeAI
# from agents.code_generator.state import CodeGenState
# from agents.code_generator.prompts import SYSTEM_PROMPT_MOBILE

# # --- 4. Mobile Generator Logic ---
# # class MobileGenNodes:
# #     def __init__(self, model: ChatGoogleGenerativeAI):
# #         self.model = model
# #
# #     async def generate_code(self, state: CodeGenState) -> dict[str, Any]:
# #         # Аналогічно Web, але інші промпти
# #         messages = [
# #             SystemMessage(content=SYSTEM_PROMPT_MOBILE),
# #             HumanMessage(
# #                 content=f"""
# #                 Context: {state["mobile_docs"]}
# #                 Data: {json.dumps(state["figma_json"])}
# #             """
# #             ),
# #         ]
# #
# #         response = await self.model.ainvoke(messages)
# #
# #         return {
# #             "mobile_code": response.content,
# #             "status_history": [
# #                 {
# #                     "timestamp": datetime.now().isoformat(),
# #                     "scope": "mobile",
# #                     "status": "success",
# #                     "message": "Mobile code generated",
# #                     "details": None,
# #                 }
# #             ],
# #         }
