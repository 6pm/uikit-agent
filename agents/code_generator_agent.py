"""
Agent task which run code generation using LangGraph
"""

from langgraph.graph import END, START, MessagesState, StateGraph


def mock_llm(state: MessagesState):  # noqa: ARG001
    print("state mock_llm", state)
    return {"messages": [{"role": "ai", "content": "hello world and Slava"}]}


class CodeGeneratorAgent:
    def __init__(self):
        """Initialize agent with default values."""

        self.graph = None

    async def _initialize(self):
        """
        Async initialization method.
        Call this after creating the instance if you need async setup.
        """
        # Example: async initialization logic here
        # await self._setup_llm()
        # await self._setup_tools()

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

    async def build_graph(self):
        """
        Generate code from Figma JSON

        Args:
            json_data: Figma JSON

        Returns:
            dict: Code generation result
        """

        code_gen_graph = StateGraph(MessagesState)
        code_gen_graph.add_node(mock_llm)
        code_gen_graph.add_edge(START, "mock_llm")
        code_gen_graph.add_edge("mock_llm", END)

        self.graph = code_gen_graph.compile()

    async def generate_code(self, json_data: str) -> dict:
        """Generate code from Figma JSON data."""
        result = await self.graph.ainvoke({"messages": [{"role": "user", "content": json_data}]})
        # result = {"messages": [{"role": "ai", "content": "hello world and AAAAAAAAAA"}]}
        print("RRRRRRRRRRRRRRRRRRRR", result)
        return result

    # async def build_graph(self):
    #     # Set up Graph Builder with State
    #     graph_builder = StateGraph(State)

    #     # Add nodes
    #     graph_builder.add_node("worker", self.worker)
    #     graph_builder.add_node("tools", ToolNode(tools=self.tools))
    #     graph_builder.add_node("evaluator", self.evaluator)

    #     # Add edges
    #     graph_builder.add_conditional_edges(
    #         "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
    #     )
    #     graph_builder.add_edge("tools", "worker")
    #     graph_builder.add_conditional_edges(
    #         "evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END}
    #     )
    #     graph_builder.add_edge(START, "worker")

    #     # Compile the graph
    #     self.graph = graph_builder.compile(checkpointer=self.memory)
