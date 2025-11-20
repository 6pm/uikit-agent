"""
Pydantic models for API request validation.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FigmaNodeProperties(BaseModel):
    """Properties of a Figma node."""

    width: Optional[float] = None
    height: Optional[float] = None

    # Add other properties as needed
    # Using Dict[str, Any] to allow flexible properties
    class Config:
        extra = "allow"


class FigmaRootNode(BaseModel):
    """Root node structure from Figma."""

    id: str
    name: str
    type: str
    properties: Optional[Dict[str, Any]] = None


class ComponentRequest(BaseModel):
    """Single component request."""

    component_id: str
    name: str
    root_node: FigmaRootNode


class CodeGenerationRequest(BaseModel):
    """Request model for code generation endpoint."""

    request: List[ComponentRequest] = Field(
        ..., description="List of components to generate code for"
    )
    target_framework: str = Field(
        default="react", description="Target framework (react, vue, etc.)"
    )
    style_approach: str = Field(
        default="tailwind", description="Styling approach (tailwind, css, etc.)"
    )
