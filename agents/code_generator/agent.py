from huey.utils import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph

from agents.code_generator.state import CodeGenState
from src.logger_config import logger

from .mcp_client import MCPClient
from .nodes import (
    InputValidationNodes,
    MCPContextRetrievalNode,
    # MobileGenNodes,
    # WebGenNodes,
)


class CodeGeneratorAgent:
    """
    Orchestrator - knows how to set up the system (which model to take, which temperature to set).
    It is responsible for initializing the system and launching the agent.
    """

    def __init__(self):
        """Initialize agent with default values."""
        self.graph = None
        self.gemini_model = None

        # configure MCP clients
        self.mcp_web_client = MCPClient("node_modules/@patrianna/uikit/dist/mcp-server/server.js")
        self.mcp_mobile_client = None

    async def __aenter__(self):
        """
        Ініціалізація ресурсів при вході в блок.
        """
        # 1. Підключаємо MCP клієнти (теж через exit stack або вручну enter)
        # Тут ми каскадно викликаємо aenter клієнтів
        await self.mcp_web_client.__aenter__()
        if self.mcp_mobile_client:
            await self.mcp_mobile_client.__aenter__()

        # 2. Ініціалізуємо модель
        await self.init_gemini_model()

        # 3. Будуємо граф (тепер це безпечно, бо MCP підключені)
        await self.build_graph()

        return self

    async def init_gemini_model(self):
        """
        Initialize Gemini model.
        In the future there will be several node classes (ValidationNodes, RefactoringNodes).
        It is better to create one model instance in the Orchestrator and share it with all nodes,
        rather than having each node create its own connection.
        """
        self.gemini_model = ChatGoogleGenerativeAI(
            model=os.getenv("MODEL_CODEGEN") or "gemini-2.5-pro",
            temperature=0.2,
            max_retries=2,
        )

    async def build_graph(self):
        """
        Будує спрямований ациклічний граф (DAG) для генерації коду.
        Включає етапи: Валідація -> Контекст -> (Веб | Мобайл) -> Лінтери -> Фініш.
        """
        # 1. Ініціалізація класів нод із залежностями
        input_nodes = InputValidationNodes()

        # Передаємо обидва MCP клієнти
        mcp_nodes = MCPContextRetrievalNode(web_client=self.mcp_web_client, mobile_client=self.mcp_mobile_client)

        # Передаємо модель (можна біндити тули, якщо треба, але ми використовуємо MCP окремо)
        # web_nodes = WebGenNodes(self.gemini_model)
        # mobile_nodes = MobileGenNodes(self.gemini_model)

        # 2. Створення графа зі типізованим станом
        workflow = StateGraph(CodeGenState)

        # --- Додавання Нод (Nodes) ---

        # Спільні етапи
        workflow.add_node("validate_input", input_nodes.validate_input)
        workflow.add_node("retrieve_mcp_context", mcp_nodes.retrieve_context)

        # Гілка Web
        # workflow.add_node("generate_web", web_nodes.generate_code)
        # workflow.add_node("lint_web", web_nodes.run_linter)

        # Гілка Mobile
        # workflow.add_node("generate_mobile", mobile_nodes.generate_code)
        # workflow.add_node("lint_mobile", mobile_nodes.run_linter)

        # --- Побудова Зв'язків (Edges) ---

        # Старт -> Валідація
        workflow.add_edge(START, "validate_input")

        # Умовний перехід: Якщо валідація провалилась — кінець, інакше — за контекстом
        workflow.add_conditional_edges(
            "validate_input",
            input_nodes.should_continue,  # Функція, яка приймає рішення чи йти далі чи завершити виконання якщо є помилка у валідації
            {  # Мапа: {що_повернула_функція: куди_йти}
                "retrieve_mcp_context": "retrieve_mcp_context",
                END: END,
            },
        )

        # TODO: це тільки для тесту проміжних 2 викликів щоб закінчити граф
        workflow.add_edge("retrieve_mcp_context", END)

        # РОЗГАЛУЖЕННЯ (Fork): Після контексту запускаємо обидві гілки паралельно
        # workflow.add_edge("retrieve_mcp_context", "generate_web")
        # workflow.add_edge("retrieve_mcp_context", "generate_mobile")

        # # Ланцюжок Web
        # workflow.add_edge("generate_web", "lint_web")
        # workflow.add_edge("lint_web", END)

        # # Ланцюжок Mobile
        # workflow.add_edge("generate_mobile", "lint_mobile")
        # workflow.add_edge("lint_mobile", END)

        # 3. Компіляція графа
        self.graph = workflow.compile()
        logger.info("CodeGen Graph built successfully.")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Очистка ресурсів.
        """
        # Закриваємо клієнти
        if self.mcp_web_client:
            await self.mcp_web_client.__aexit__(exc_type, exc_val, exc_tb)
        if self.mcp_mobile_client:
            await self.mcp_mobile_client.__aexit__(exc_type, exc_val, exc_tb)

        logger.info("Agent resources released.")

    # async def generate_web_code(self, request_data: CodeGenerationRequest) -> dict[str, Any]:
    #     """
    #     Generate code from Figma JSON data using LangGraph.
    #     This is main function for launching the agent.
    #     As a result it will return generated code and status of the task.

    #     Returns:
    #         dict[str, Any]: Dictionary with generated code and status of the task
    #     """

    #     try:
    #         # Initialization of messages, system prompt and status
    #         inputs = {
    #             "messages": [
    #                 SystemMessage(content=SYSTEM_PROMPT_WEB),
    #                 HumanMessage(
    #                     content=f"""
    #                     {request_data.userPrompt or ""} \n {USER_MESSAGE_WEB_START} \n
    #                     {json.dumps(request_data.figmaJson, indent=2)}"""
    #                 ),
    #             ]
    #         }

    #         # Invoke graph
    #         result = await self.graph.ainvoke(inputs)

    #         if result.get("status") == "error":
    #             print("Error! generate_web_code")
    #             return {"error": result.get("error"), "status": "error"}

    #         # Get last message
    #         last_message = result["messages"][-1]

    #         return {"content": last_message.content, "status": "completed"}

    #     except Exception as e:
    #         logger.error("Error in generate_web_code: %s", e, exc_info=True)
    #         return {"error": str(e)}
