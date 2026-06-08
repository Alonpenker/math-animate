from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from llm_knowledge.document_models import (
    KnowledgeDocument,
    KnowledgeDocumentSeed,
    KnowledgeType,
    PriorityType,
    TemplateDocumentSeed,
)
from llm_knowledge.skill_documents import TEMPLATE_TITLES


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
TemplateReference = Literal[*TEMPLATE_TITLES]


class TemplateBlueprint(BaseModel):
    name: str = Field(..., pattern=r"^[a-z][a-z0-9_]*$", max_length=80)
    reference: TemplateReference
    parameters: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_state_parameter(self):
        state = self.parameters.get("state")
        if not isinstance(state, str) or not state:
            raise ValueError("template parameters must include a non-empty string state")
        return self


class TemplateActionBlueprint(BaseModel):
    target: str = Field(..., pattern=r"^[a-z][a-z0-9_]*$", max_length=80)
    action: str = Field(..., pattern=r"^[a-z][a-z0-9_]*$", max_length=80)
    parameters: dict[str, Any] = Field(default_factory=dict)


class SubsceneBlueprint(BaseModel):
    id: str = Field(..., pattern=r"^[a-z][a-z0-9_]*$", max_length=80)
    purpose: str = Field(..., max_length=400)
    layout: VisualKitLayoutTemplate
    transition: SubsceneTransition
    templates: list[TemplateBlueprint] = Field(..., min_length=1, max_length=2)
    actions: list[TemplateActionBlueprint] = Field(default_factory=list, max_length=8)
    caption: str | None = Field(default=None, max_length=120)
    bottom_text: str | None = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def validate_template_contract(self):
        expected_count = 1 if self.layout == "center" else 2
        if len(self.templates) != expected_count:
            raise ValueError(
                f"{self.layout} layout requires exactly {expected_count} template(s)"
            )

        names = [template.name for template in self.templates]
        if len(names) != len(set(names)):
            raise ValueError("template names must be unique within a subscene")

        missing_targets = sorted({
            action.target for action in self.actions if action.target not in names
        })
        if missing_targets:
            raise ValueError(
                f"action targets must match template names: {missing_targets}"
            )
        return self


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
