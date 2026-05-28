from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ScenePlan(BaseModel):
    learning_objective: str
    visual_storyboard: str
    voice_notes: str
    scene_number: int = Field(..., ge=-1, le=3)


class VideoPlan(BaseModel):
    scenes: list[ScenePlan]

    def to_prompt_text(self) -> str:
        return self.model_dump_json(indent=2)


class KnowledgeType(str, Enum):
    SKILL = "skill"
    RULE = "rule"
    TEMPLATE = "template"
    EXAMPLE = "example"


PriorityType = Literal["core", "recommended", "optional"]


class KnowledgeDocument(BaseModel):
    document_id: UUID
    doc_type: KnowledgeType
    title: str
    category: Any
    priority: PriorityType = "optional"
    tags: list[str] = Field(default_factory=list)

    def to_metadata(self) -> str:
        category = getattr(self.category, "value", self.category)
        tags = ", ".join(self.tags) if self.tags else "none"
        return (
            f"- {self.title} "
            f"(type={self.doc_type.value}, category={category}, "
            f"priority={self.priority}, tags={tags})"
        )


class KnowledgeDocumentSeed(KnowledgeDocument):
    path: str
