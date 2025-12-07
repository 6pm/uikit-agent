from pydantic import BaseModel, Json


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
