"""Types for code generation API requests and responses."""

import operator
from typing import Annotated

from pydantic import BaseModel, Json

from agents.code_generator.state import StatusEvent


class CodeGenerationRequest(BaseModel):
    """
    Request model for the '/generate-code' route.
    Validates all input data from the API request.
    """

    figmaJson: dict | list | Json  # Support JSON and parsed object (Task re-hydration)
    componentName: str
    userPrompt: str | None = None
    userId: str
    userName: str


# ----
class CodeGenerationResponse(BaseModel):
    """
    Response model for the '/generate-code' route.
    """

    message: str
    task_id: str
    status: str


class CodeGenTaskResult(BaseModel):
    """
    Result of the code generation task which will be written to Redis.
    It contains few felds from LangGraph workflow state.
    """

    status_history: Annotated[list[StatusEvent], operator.add]

    # Generated code
    web_code: str | None
    mobile_code: str | None
