import operator
from typing import Annotated

from pydantic import BaseModel, Json

from agents.code_generator.state import StatusEvent


class CodeGenerationRequest(BaseModel):
    # Support both JSON string (API) and parsed object (Task re-hydration)
    figmaJson: dict | list | Json
    componentName: str
    userPrompt: str | None = None


# ----
class CodeGenerationResponse(BaseModel):
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
