from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator
from app.llm_knowledge.skill_documents import TEMPLATE_TITLES

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
    layout: Literal["center", "split"]
    transition: Literal["show", "transform"]
    templates: list[TemplateBlueprint] = Field(..., min_length=1, max_length=2)
    actions: list[TemplateActionBlueprint] = Field(default_factory=list, max_length=8)
    caption: str | None = Field(default=None, max_length=120)
    bottom_text: str | None = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def validate_template_contract(self):
        if self.layout == "center" and len(self.templates) != 1:
            raise ValueError("center layout requires exactly 1 template")
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
