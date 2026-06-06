from enum import Enum
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ScenePlan(BaseModel):
    learning_objective: str = Field(..., max_length=400)
    visual_storyboard: str = Field(..., max_length=3000)
    voice_notes: str = Field(..., max_length=3000)
    scene_number: int = Field(..., ge=-1, le=3)


class VideoPlan(BaseModel):
    scenes: list[ScenePlan]

    def to_prompt_text(self) -> str:
        return self.model_dump_json(indent=2)


VisualKitLayoutTemplate = Literal[
    "center",
    "split",
]
SubsceneTransition = Literal[
    "show",
    "transform",
]


class SubsceneBlueprint(BaseModel):
    id: str = Field(..., pattern=r"^[a-z][a-z0-9_]*$", max_length=80)
    purpose: str = Field(..., max_length=400)
    builder_name: str = Field(..., pattern=r"^build_[a-z][a-z0-9_]*$", max_length=80)
    builder_shape: str = Field(..., max_length=1200)
    layout: VisualKitLayoutTemplate
    transition: SubsceneTransition
    references: list[Annotated[str, Field(max_length=120)]] = Field(
        ...,
        max_length=6,
    )
    caption: str | None = Field(default=None, max_length=120)
    bottom_text: str | None = Field(default=None, max_length=120)


class SceneCodeBlueprint(BaseModel):
    scene_number: int = Field(..., ge=1, le=3)
    scene_title: str = Field(..., max_length=120)
    subscenes: list[SubsceneBlueprint] = Field(..., min_length=1, max_length=8)


class CodePlan(BaseModel):
    scenes: list[SceneCodeBlueprint] = Field(..., min_length=1, max_length=3)

    def to_prompt_text(self) -> str:
        return self.model_dump_json(indent=2)


CodeQaDecision = Literal["pass", "block"]
CodeQaSeverity = Literal["blocker", "warning"]
CodeQaCategory = Literal[
    "stale_coordinate_labels",
    "detached_semantic_groups",
    "major_object_without_vgroup",
    "created_but_invisible_required_object",
    "offscreen_or_clipped_text",
    "negative_buffer_major_layout",
    "fake_square_on_side_geometry",
    "invalid_mathematical_object_claim",
    "fake_proof_continuity",
    "unbounded_text_layout_budget",
    "contrast_failure",
    "other_code_visible_visual_defect",
]


class CodeQaIssue(BaseModel):
    severity: CodeQaSeverity
    category: CodeQaCategory
    scene_number: int = Field(
        ...,
        ge=0,
        description="Use 0 for file-level helpers or shared layout defects.",
    )
    line_refs: list[int] = Field(default_factory=list, max_length=8)
    evidence: str = Field(..., max_length=500)
    visual_risk: str = Field(..., max_length=500)
    required_fix: str = Field(..., max_length=400)


class CodeQaReport(BaseModel):
    decision: CodeQaDecision
    summary: str = Field(..., max_length=600)
    issues: list[CodeQaIssue] = Field(default_factory=list, max_length=3)
    fix_instructions: str = Field(..., max_length=800)


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
    planning_capability: str | None = None
