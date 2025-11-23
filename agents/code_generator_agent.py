"""
Agent task which run code generation using LangGraph
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

# imports for Gemini model
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, MessagesState, StateGraph

from schemas.ai_models.test_ai_response import TestAIResponse
from schemas.api.code_generation_types import CodeGenerationRequest

logger = logging.getLogger(__name__)


def mock_llm(state: MessagesState) -> TestAIResponse:
    print("state mock_llm", state)
    return {"messages": [{"role": "ai", "content": "hello world and Slava"}]}


class CodeGeneratorAgent:
    def __init__(self):
        """Initialize agent with default values."""

        self.graph = None
        self.gemini_model = None

    async def _initialize(self):
        """
        Async initialization method.
        Call this after creating the instance if you need async setup.
        """
        # Example: async initialization logic here
        # await self._setup_llm()
        # await self._setup_tools()

        await self.init_gemini_model()
        await self.build_graph()

    @classmethod
    async def create(cls):
        """
        Factory method for async initialization.

        Usage:
            agent = await CodeGeneratorAgent.create()

        Returns:
            CodeGeneratorAgent: Initialized agent instance
        """
        instance = cls()
        await instance._initialize()
        return instance

    async def init_gemini_model(self):
        """
        Initialize Gemini model
        """

        self.gemini_model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0,  # 0 для кодингу краще (більш детерміновано)
            max_retries=2,
        )

    # реальна нода що викликає Gemini модель
    def call_model(self, state: MessagesState):
        """
        Invokes the Gemini model with the current state messages.
        """
        messages = state["messages"]

        # Тут можна додати System Message, якщо його немає в історії
        # Але краще це робити при формуванні запиту (див. нижче)

        logger.info("🤖 Calling Gemini model...")
        response = self.gemini_model.invoke(messages)

        # LangGraph автоматично додасть це повідомлення до історії (append)
        return {"messages": [response]}

    async def build_graph(self):
        """
        Generate code from Figma JSON

        Args:
            json_data: Figma JSON

        Returns:
            dict: Code generation result
        """

        # Set up Graph Builder with State
        graph_builder = StateGraph(MessagesState)

        # Додаємо реальну ноду
        # Зверніть увагу: ми передаємо self.call_model, бо це метод класу
        graph_builder.add_node("generate_code", self.call_model)

        # Будуємо простий потік
        graph_builder.add_edge(START, "generate_code")
        graph_builder.add_edge("generate_code", END)
        # end test mock code

        # ------------------------------------------------------------------------------------------------

        # # Add nodes
        # graph_builder.add_node("worker", self.worker)
        # graph_builder.add_node("tools", ToolNode(tools=self.tools))
        # graph_builder.add_node("evaluator", self.evaluator)

        # # Add edges
        # graph_builder.add_conditional_edges(
        #     "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
        # )
        # graph_builder.add_edge("tools", "worker")
        # graph_builder.add_conditional_edges(
        #     "evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END}
        # )
        # graph_builder.add_edge(START, "worker")

        # # Compile the graph
        # self.graph = graph_builder.compile(checkpointer=self.memory)

        self.graph = graph_builder.compile()

    async def generate_code(self, request_data: CodeGenerationRequest) -> dict[str, Any]:
        """
        Generate code from Figma JSON data.
        """
        # Конвертуємо запит в JSON-рядок
        message_str = request_data.model_dump_json()

        # 5. Формуємо правильний вхідний контекст
        # Додаємо SystemMessage, щоб задати роль моделі
        system_prompt = """You are an expert Frontend Developer.
Your task is to generate clean, production-ready code based on the provided Figma JSON data.
Do not include conversational filler, output only the code or JSON result."""

        inputs = {"messages": [SystemMessage(content=system_prompt), HumanMessage(content=message_str)]}

        # Викликаємо граф
        result = await self.graph.ainvoke(inputs)

        # result['messages'][-1] буде останньою відповіддю від AI
        last_message = result["messages"][-1]

        return {
            "content": last_message.content,
            # "usage": last_message.usage_metadata # Якщо треба статистика токенів
        }
