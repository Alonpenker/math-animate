"""Tests for CodePlan schema validators (Unit 2 from plan)."""
import pytest
from pydantic import ValidationError

from app.schemas.code_plan import (
    CodePlan,
    SceneCodeBlueprint,
    SubsceneBlueprint,
    TemplateActionBlueprint,
    TemplateBlueprint,
)


def _make_template(name: str = "eq", reference: str = "Equation Template") -> dict:
    return {"name": name, "reference": reference, "parameters": {"state": "base"}}


def _make_subscene(**overrides) -> dict:
    base = {
        "id": "intro",
        "purpose": "Show the equation",
        "layout": "center",
        "transition": "show",
        "templates": [_make_template()],
        "actions": [],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# TemplateBlueprint — state parameter validation
# ---------------------------------------------------------------------------

def test_template_blueprint_rejects_missing_state():
    with pytest.raises(ValidationError, match="non-empty string state"):
        TemplateBlueprint(
            name="eq", reference="Equation Template", parameters={}
        )


def test_template_blueprint_rejects_empty_state():
    with pytest.raises(ValidationError, match="non-empty string state"):
        TemplateBlueprint(
            name="eq", reference="Equation Template", parameters={"state": ""}
        )


def test_template_blueprint_rejects_non_string_state():
    with pytest.raises(ValidationError, match="non-empty string state"):
        TemplateBlueprint(
            name="eq", reference="Equation Template", parameters={"state": 42}
        )


def test_template_blueprint_accepts_valid_state():
    t = TemplateBlueprint(
        name="eq", reference="Equation Template", parameters={"state": "base"}
    )
    assert t.parameters["state"] == "base"


# ---------------------------------------------------------------------------
# SubsceneBlueprint — layout vs template count
# ---------------------------------------------------------------------------

def test_subscene_rejects_center_with_two_templates():
    with pytest.raises(ValidationError, match="center layout requires exactly 1 template"):
        SubsceneBlueprint(**_make_subscene(
            layout="center",
            templates=[_make_template("t1"), _make_template("t2", "Number Line Template")],
        ))


def test_subscene_accepts_center_with_one_template():
    s = SubsceneBlueprint(**_make_subscene(layout="center", templates=[_make_template()]))
    assert s.layout == "center"
    assert len(s.templates) == 1


def test_subscene_accepts_split_with_two_templates():
    s = SubsceneBlueprint(**_make_subscene(
        layout="split",
        templates=[_make_template("t1"), _make_template("t2", "Number Line Template")],
    ))
    assert s.layout == "split"
    assert len(s.templates) == 2


# ---------------------------------------------------------------------------
# SubsceneBlueprint — action target validation
# ---------------------------------------------------------------------------

def test_subscene_rejects_action_targeting_nonexistent_template():
    with pytest.raises(ValidationError, match="action targets must match template names"):
        SubsceneBlueprint(**_make_subscene(
            templates=[_make_template("eq")],
            actions=[{"target": "ghost", "action": "highlight", "parameters": {}}],
        ))


def test_subscene_accepts_action_targeting_existing_template():
    s = SubsceneBlueprint(**_make_subscene(
        templates=[_make_template("eq")],
        actions=[{"target": "eq", "action": "highlight", "parameters": {}}],
    ))
    assert s.actions[0].target == "eq"


# ---------------------------------------------------------------------------
# TemplateReference — unknown title rejected
# ---------------------------------------------------------------------------

def test_template_blueprint_rejects_unknown_reference():
    with pytest.raises(ValidationError):
        TemplateBlueprint(
            name="bad",
            reference="NonExistentTemplate",
            parameters={"state": "x"},
        )
