"""
Agent task which run code generation using LangGraph
"""

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

        result = { 'message': 'code generated successfully' }
        return result
