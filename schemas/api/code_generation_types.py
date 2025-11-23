from pydantic import BaseModel


class RootNodeProperties(BaseModel):
    width: float
    height: float


class RootNode(BaseModel):
    id: str
    name: str
    type: str
    properties: RootNodeProperties


class ComponentRequest(BaseModel):
    component_id: str
    name: str
    root_node: RootNode


class CodeGenerationRequest(BaseModel):
    request: list[ComponentRequest]
    target_framework: str
    style_approach: str


# ----
class CodeGenerationResponse(BaseModel):
    message: str
    task_id: str
    status: str
