import logging
from typing import Any

from .state import CodeGenState

logger = logging.getLogger(__name__)


class CodeGenNodes:
    """
    Знає ЩО робити з моделлю (відправити промпт, розпарсити відповідь).
    Він просто отримує інструмент і працює ним.
    Тут використовується Dependency Injection принцип.
    """

    def __init__(self, model):
        self.model = model

    def call_model(self, state: CodeGenState) -> dict[str, Any]:
        """
        Invokes the Gemini model with the current state messages.
        """
        messages = state["messages"]

        logger.info("🤖 Calling Gemini model...")
        response = self.model.invoke(messages)

        # LangGraph automatically appends this message to history
        # We also update the status
        return {"messages": [response], "status": "completed"}
