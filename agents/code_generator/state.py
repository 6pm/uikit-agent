"""
Main state for the code generation agent.
"""

import operator
from typing import Annotated, Literal, TypedDict


class StatusEvent(TypedDict):
    """
    Structure of a single status event.

    Attributes:
        timestamp: Timestamp of the event.
        scope: The source of the status (system, web, or mobile).
        status: The status of the event (pending, success, error, info).
        message: A human-readable message intended for the UI.
        details: Technical details (e.g., linter errors), if any.
    """

    timestamp: str
    scope: Literal["common", "system", "web", "mobile"]
    status: Literal["pending", "success", "error", "info"]
    message: str
    details: dict | None


class CodeGenState(TypedDict):
    """
    State for the code generation workflow.

    Attributes:
        figma_json: The input Figma JSON data (immutable).
        user_prompt: The user's prompt or instructions.
        web_docs: Context documentation for web code generation.
        mobile_docs: Context documentation for mobile code generation.
        status_history: A list of status events, accumulated over time.
        web_code: The generated web code.
        mobile_code: The generated mobile code.
    """

    # Input data (immutable)
    figma_json: dict
    component_name: str
    user_prompt: str | None

    # Context (populated by Context Retrieval)
    web_docs: str | None
    mobile_docs: str | None

    # List accumulating history. operator.add appends new elements to the existing list.
    status_history: Annotated[list[StatusEvent], operator.add]

    # Generated code
    web_code: str | None
    mobile_code: str | None
