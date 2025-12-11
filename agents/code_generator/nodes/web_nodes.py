from typing import Any

# Імпортуємо базовий клас звідки ти його зберіг
from agents.code_generator.nodes.base_codegen_nodes import BaseCodeGenNodes
from agents.code_generator.prompts import FIX_LINTER_PROMPT_WEB, FIX_LINTER_PROMPT_WEB_SYSTEM, SYSTEM_PROMPT_WEB, USER_MESSAGE_WEB_START


class WebPipelineNodes(BaseCodeGenNodes):
    platform = "web"

    def _get_file_path(self, component_name: str) -> str:
        return f"src/app/preview/{component_name}/page.tsx"

    def _get_system_prompt(self) -> str:
        return SYSTEM_PROMPT_WEB

    def _get_user_prompt_start(self) -> str:
        return USER_MESSAGE_WEB_START

    def _get_fix_prompts(self) -> tuple[str, Any]:
        return FIX_LINTER_PROMPT_WEB_SYSTEM, FIX_LINTER_PROMPT_WEB
