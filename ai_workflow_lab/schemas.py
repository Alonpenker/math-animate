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


class RegionPlan(BaseModel):
    role: str = Field(..., max_length=120)
    position: str = Field(..., max_length=240)
    max_width: str = Field(..., max_length=160)
    max_height: str = Field(..., max_length=160)
    fit_instruction: str = Field(..., max_length=500)


class LayoutPlan(BaseModel):
    primary_region: RegionPlan
    reserved_regions: list[RegionPlan] = Field(default_factory=list, max_length=6)
    forbidden_layout: list[str] = Field(default_factory=list, max_length=8)


class VisualBlock(BaseModel):
    id: str = Field(..., max_length=120)
    type: str = Field(..., max_length=120)
    contains: list[str] = Field(default_factory=list, max_length=20)
    placement: str = Field(..., max_length=400)
    visual_priority: str = Field(..., max_length=240)


class TextBudget(BaseModel):
    max_visible_text_blocks: int = Field(..., ge=0, le=12)
    longest_text_allowed: str = Field(..., max_length=240)
    overflow_strategy: str = Field(..., max_length=500)


class AnimationBeat(BaseModel):
    beat: str = Field(..., max_length=600)
    visible_after: list[str] = Field(default_factory=list, max_length=30)


class SubsceneBlueprint(BaseModel):
    id: str = Field(..., max_length=120)
    visual_goal: str = Field(..., max_length=600)
    layout: LayoutPlan
    visual_blocks: list[VisualBlock] = Field(..., min_length=1, max_length=12)
    text_budget: TextBudget
    animation_beats: list[AnimationBeat] = Field(..., min_length=1, max_length=12)
    clear_after: list[str] = Field(default_factory=list, max_length=30)


class SceneCodeBlueprint(BaseModel):
    scene_number: int = Field(..., ge=1, le=3)
    scene_goal: str = Field(..., max_length=600)
    creative_direction: str = Field(..., max_length=600)
    subscene_split_rationale: str = Field(..., max_length=800)
    subscenes: list[SubsceneBlueprint] = Field(..., min_length=1, max_length=8)


class HelperContract(BaseModel):
    name: str = Field(..., max_length=120)
    purpose: str = Field(..., max_length=500)
    use_case: str = Field(..., max_length=500)
    inputs: list[str] = Field(default_factory=list, max_length=12)
    returns: list[str] = Field(default_factory=list, max_length=12)
    rules: list[str] = Field(default_factory=list, max_length=8)


class CodePlan(BaseModel):
    scene_blueprints: list[SceneCodeBlueprint] = Field(..., min_length=1, max_length=3)
    shared_helpers_needed: list[HelperContract] = Field(default_factory=list, max_length=8)
    codegen_priorities: list[str] = Field(default_factory=list, max_length=10)

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
