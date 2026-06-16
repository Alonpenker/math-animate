from pathlib import Path

from app.llm_knowledge.skill_documents import LLMKNOWLEDGE_DIR, read_knowledge_file
from app.schemas.knowledge import TemplateDocumentSeed

_VISUAL_KIT_PATH = LLMKNOWLEDGE_DIR / "manim_skill" / "visual_kit.py"
_LESSON_BODY_MARKER = "# Lesson-specific generated code\n\n"


def assemble_file(
    lesson_body: str,
    referenced_templates: list[TemplateDocumentSeed],
) -> str:
    visual_kit = _VISUAL_KIT_PATH.read_text(encoding="utf-8").rstrip()
    template_sections = "\n\n\n".join(
        (
            f"# Authoritative template: {template.title}\n\n"
            f"{read_knowledge_file(template.path).rstrip()}"
        )
        for template in referenced_templates
    )
    body = lesson_body.strip()
    sections = [visual_kit]
    if template_sections:
        sections.append(template_sections)
    sections.append(f"{_LESSON_BODY_MARKER}{body}")
    return "\n\n\n".join(sections) + "\n"


def extract_lesson_body(assembled_code: str) -> str:
    idx = assembled_code.find(_LESSON_BODY_MARKER)
    if idx >= 0:
        return assembled_code[idx + len(_LESSON_BODY_MARKER):].rstrip("\n")
    return assembled_code
