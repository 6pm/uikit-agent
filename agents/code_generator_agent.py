"""
Agent task which run code generation using LangGraph
"""

from langgraph.graph import END, START, MessagesState, StateGraph


def mock_llm(state: MessagesState):
    return {"messages": [{"role": "ai", "content": "hello world"}]}


class CodeGeneratorAgent:
    def generate(self, json_data: str) -> dict:
        """
        Generate code from Figma JSON

        Args:
            json_data: Figma JSON

        Returns:
            dict: Code generation result
        """

        print(f"CodeGeneratorAgent: {json_data}")

        codeGenGraph = StateGraph(MessagesState)
        codeGenGraph.add_node(mock_llm)
        codeGenGraph.add_edge(START, "mock_llm")
        codeGenGraph.add_edge("mock_llm", END)
        codeGenGraph = codeGenGraph.compile()

        result = {"message": "code generated successfully"}
        return result
