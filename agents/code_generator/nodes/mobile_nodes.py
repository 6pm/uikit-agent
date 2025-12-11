from typing import Any

from agents.code_generator.nodes.base_codegen_nodes import BaseCodeGenNodes
from agents.code_generator.prompts import (
    FIX_LINTER_PROMPT_MOBILE,
    FIX_LINTER_PROMPT_MOBILE_SYSTEM,
    SYSTEM_PROMPT_MOBILE,
    USER_MESSAGE_MOBILE_START,
)


class MobilePipelineNodes(BaseCodeGenNodes):
    platform = "mobile"

    def _get_file_path(self, component_name: str) -> str:
        # TODO: for React Native the path is different
        return f"app/(screens)/{component_name}.tsx"

    def _get_system_prompt(self) -> str:
        return SYSTEM_PROMPT_MOBILE

    def _get_user_prompt_start(self) -> str:
        return USER_MESSAGE_MOBILE_START

    def _get_fix_prompts(self) -> tuple[str, Any]:
        return FIX_LINTER_PROMPT_MOBILE_SYSTEM, FIX_LINTER_PROMPT_MOBILE
