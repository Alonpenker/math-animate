"""Tests for node implementations: assemble_file, fix node, document_selection node."""
from dataclasses import dataclass
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.domain.job_state import JobStatus
from app.llm_knowledge.skill_documents import CORE_DOCUMENTS, LLMKNOWLEDGE_DIR, REGISTRY_BY_ID
from app.schemas.code_plan import CodePlan, SceneCodeBlueprint, SubsceneBlueprint, TemplateBlueprint
from app.schemas.knowledge import CandidateResult, KnowledgeDocument, KnowledgeType, TemplateDocumentSeed
from app.schemas.scene_plan import ScenePlan
from app.schemas.user_request import UserRequest
from app.schemas.video_plan import VideoPlan
from app.services.nodes._context import CodegenContext


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_video_plan():
    return VideoPlan(
        scenes=[ScenePlan(
            learning_objective="Learn to solve equations",
            visual_storyboard="Show the equation step by step",
            voice_notes="An equation balances both sides",
            scene_number=1,
        )]
    )


@pytest.fixture
def sample_user_request():
    return UserRequest(
        topic="Solving linear equations",
        misconceptions=[],
        constraints=[],
        examples=[],
        number_of_scenes=1,
    )


@pytest.fixture
def sample_code_plan():
    return CodePlan(
        scenes=[SceneCodeBlueprint(
            scene_number=1,
            scene_title="Intro",
            subscenes=[SubsceneBlueprint(
                id="intro",
                purpose="Show the equation",
                layout="center",
                transition="show",
                templates=[TemplateBlueprint(
                    name="eq",
                    reference="Equation Template",
                    parameters={"state": "base"},
                )],
                actions=[],
            )],
        )]
    )


@pytest.fixture
def ctx():
    return CodegenContext(job_id=uuid4(), current_status=JobStatus.CODEGEN)


# ---------------------------------------------------------------------------
# Unit 8: assemble_file output order
# ---------------------------------------------------------------------------

def test_assemble_file_produces_visual_kit_then_templates_then_lesson_body():
    from app.services.nodes._assemble import assemble_file

    template_seed = next(
        e for e in REGISTRY_BY_ID.values()
        if isinstance(e, TemplateDocumentSeed) and e.title == "Equation Template"
    )
    lesson_body = "from manim import *\nclass Scene1(SafeScene): pass"

    result = assemble_file(lesson_body, [template_seed])

    visual_kit_source = (LLMKNOWLEDGE_DIR / "manim_skill" / "visual_kit.py").read_text(encoding="utf-8")
    template_source = (LLMKNOWLEDGE_DIR / template_seed.path).read_text(encoding="utf-8")

    # Order: visual_kit → template → lesson body
    vk_pos = result.find(visual_kit_source[:80])
    tmpl_pos = result.find(template_source[:80])
    body_pos = result.find(lesson_body.strip()[:40])

    assert vk_pos != -1, "visual_kit.py content not found in assembled output"
    assert tmpl_pos != -1, "template source not found in assembled output"
    assert body_pos != -1, "lesson body not found in assembled output"
    assert vk_pos < tmpl_pos < body_pos, (
        f"Expected visual_kit ({vk_pos}) < template ({tmpl_pos}) < body ({body_pos})"
    )


def test_assemble_file_without_templates_has_no_template_section():
    from app.services.nodes._assemble import assemble_file

    lesson_body = "from manim import *\nclass Scene1(SafeScene): pass"
    result = assemble_file(lesson_body, [])

    assert "# Authoritative template:" not in result
    assert lesson_body.strip() in result


def test_assemble_file_ends_with_newline():
    from app.services.nodes._assemble import assemble_file

    lesson_body = "from manim import *\nclass Scene1(SafeScene): pass"
    result = assemble_file(lesson_body, [])

    assert result.endswith("\n")


def test_extract_lesson_body_roundtrip():
    from app.services.nodes._assemble import assemble_file, extract_lesson_body

    template_seed = next(
        e for e in REGISTRY_BY_ID.values()
        if isinstance(e, TemplateDocumentSeed) and e.title == "Equation Template"
    )
    original_body = "from manim import *\nclass Scene1(SafeScene): pass"
    assembled = assemble_file(original_body, [template_seed])
    extracted = extract_lesson_body(assembled)

    assert extracted == original_body.strip()


def test_verify_node_checks_lesson_body_then_dry_runs_assembled_code(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    ctx: CodegenContext,
    sample_video_plan: VideoPlan,
):
    import app.services.nodes._context as ctx_module
    import app.services.nodes.verify as verify_module
    from app.services.nodes._assemble import assemble_file

    lesson_body = "from manim import *\nclass Scene1(SafeScene): pass"
    assembled = assemble_file(lesson_body, [])
    static_inputs: list[str] = []
    dry_run_inputs: list[str] = []

    monkeypatch.setattr(ctx_module, "transition_job", lambda *a: None)
    monkeypatch.setattr(verify_module.PathNames, "TMP_RENDER_FOLDER", str(tmp_path))
    monkeypatch.setattr(
        verify_module,
        "verify_code",
        lambda code, expected_scene_count=None: (
            static_inputs.append((code, expected_scene_count)) or None
        ),
    )

    def fake_dry_run(code_path, media_dir):
        dry_run_inputs.append(code_path.read_text(encoding="utf-8"))
        return True, "", True

    monkeypatch.setattr(verify_module, "dry_run_docker", fake_dry_run)
    ctx.current_status = JobStatus.CODED

    result = verify_module.make_verify_node(ctx)({
        "code": assembled,
        "fix_attempt": 0,
        "plan": sample_video_plan,
    })

    assert static_inputs == [(lesson_body, 1)]
    assert dry_run_inputs == [assembled]
    assert result["verification_failure"] == ""


# ---------------------------------------------------------------------------
# Unit 10: fix node human message construction
# ---------------------------------------------------------------------------

def test_fix_node_human_message_contains_all_required_parts(
    monkeypatch: pytest.MonkeyPatch,
    ctx: CodegenContext,
    sample_video_plan: VideoPlan,
    sample_user_request: UserRequest,
    sample_code_plan: CodePlan,
):
    import app.services.nodes.fix as fix_module
    import app.services.nodes._context as ctx_module
    from app.services.nodes._assemble import assemble_file
    from app.services.openrouter_service import OpenRouterTokenUsage
    from app.workers.worker_settings import MAX_FIX_ATTEMPTS

    monkeypatch.setattr(ctx_module, "transition_job", lambda *a: None)

    template_seed = next(
        e for e in REGISTRY_BY_ID.values()
        if isinstance(e, TemplateDocumentSeed) and e.title == "Equation Template"
    )
    lesson_body = "from manim import *\nclass Scene1(SafeScene): pass"
    assembled = assemble_file(lesson_body, [template_seed])

    captured_messages: list = []
    fake_usage = OpenRouterTokenUsage(input_tokens=10, output_tokens=5, reasoning_tokens=0, total_tokens=15)
    fake_response = AIMessage(content="```python\nfrom manim import *\nclass Scene1(SafeScene): pass\n```")

    def fake_invoke(*, job_id, stage, call_type, model, messages, max_tokens, reasoning_effort):
        captured_messages.extend(messages)
        return fake_response, fake_usage

    monkeypatch.setattr(fix_module.OpenRouterService, "invoke", staticmethod(fake_invoke))

    fix_attempt_in_state = 2  # simulates attempt 3 (fix_attempt+1 in node)
    state = {
        "job_id": ctx.job_id,
        "plan": sample_video_plan,
        "user_request": sample_user_request,
        "code": assembled,
        "code_plan": sample_code_plan,
        "verification_failure": "NameError: name 'x' is not defined",
        "fix_attempt": fix_attempt_in_state,
        "referenced_templates": [template_seed],
        "messages": [SystemMessage(content="some knowledge")],
        "verification_fixable": True,
    }

    make_fix_node = fix_module.make_fix_node
    node = make_fix_node(ctx)
    result = node(state)

    # Find the HumanMessage in captured messages
    human_msgs = [m for m in captured_messages if isinstance(m, HumanMessage)]
    assert human_msgs, "No HumanMessage found in fix LLM call"
    content = human_msgs[-1].content

    expected_attempt = fix_attempt_in_state + 1
    assert f"Attempt {expected_attempt} of {MAX_FIX_ATTEMPTS}" in content, \
        f"Attempt counter missing. Got: {content[:200]}"
    assert "NameError: name 'x' is not defined" in content, "Failure text missing"
    assert str(sample_user_request) in content, "User request missing"
    assert sample_video_plan.to_prompt_text()[:50] in content, "Video plan JSON missing"
    assert sample_code_plan.to_prompt_text()[:50] in content, "Code plan JSON missing"

    visual_kit_api = (LLMKNOWLEDGE_DIR / "manim_skill" / "rules" / "visual-kit-api.md").read_text()
    assert visual_kit_api[:80] in content, "Visual kit API content missing"

    assert lesson_body.strip() in content, "Lesson body missing"
    assert "# Authoritative template:" not in content, \
        "Assembled file header found — fix node should pass lesson body only, not assembled file"

    assert result["fix_attempt"] == expected_attempt
    assert "code" in result


# ---------------------------------------------------------------------------
# Unit 5: document_selection node excludes core docs from LLM prompt
# ---------------------------------------------------------------------------

def test_document_selection_excludes_core_docs_from_llm_prompt(
    monkeypatch: pytest.MonkeyPatch,
    ctx: CodegenContext,
    sample_video_plan: VideoPlan,
    sample_user_request: UserRequest,
):
    import app.services.nodes.document_selection as ds_module
    from app.services.openrouter_service import OpenRouterTokenUsage
    from app.schemas.knowledge import KnowledgeDocumentSeed
    from app.llm_knowledge.categories import RuleCategory

    # Arrange: a core doc and a non-core doc returned from retrieval.
    # The node filters candidates through REGISTRY_BY_ID, so both must have real registry IDs.
    from app.llm_knowledge.skill_documents import REGISTRY
    core_doc_seed = CORE_DOCUMENTS[0]
    non_core_seed = next(e for e in REGISTRY if e.document_id not in {d.document_id for d in CORE_DOCUMENTS})

    def _to_knowledge_doc(seed) -> KnowledgeDocument:
        return KnowledgeDocument(
            document_id=seed.document_id,
            doc_type=seed.doc_type,
            title=seed.title,
            category=seed.category,
        )

    candidate_result = CandidateResult(
        candidate_rules=[_to_knowledge_doc(core_doc_seed), _to_knowledge_doc(non_core_seed)],
        candidate_templates=[],
    )

    monkeypatch.setattr(
        ds_module.SkillRetrievalService,
        "retrieve",
        staticmethod(lambda cursor, embed_text: candidate_result),
    )

    from contextlib import contextmanager

    @contextmanager
    def fake_cursor_ctx():
        yield object()

    monkeypatch.setattr(ds_module, "get_worker_cursor", fake_cursor_ctx)

    captured_messages: list = []
    fake_usage = OpenRouterTokenUsage(input_tokens=10, output_tokens=5, reasoning_tokens=0, total_tokens=15)

    class _FakeSelected:
        selected_titles: list[str] = []

    def fake_invoke_structured(*, job_id, stage, call_type, model, messages, schema, max_tokens):
        captured_messages.extend(messages)
        return _FakeSelected(), fake_usage

    monkeypatch.setattr(
        ds_module.OpenRouterService,
        "invoke_structured",
        staticmethod(fake_invoke_structured),
    )

    node = ds_module.make_document_selection_node(ctx)
    state = {
        "job_id": ctx.job_id,
        "plan": sample_video_plan,
        "user_request": sample_user_request,
        "messages": [],
    }
    node(state)

    assert captured_messages, "No messages captured from document_selection LLM call"
    prompt_content = " ".join(
        m.content for m in captured_messages if isinstance(m, HumanMessage)
    )

    assert core_doc_seed.title not in prompt_content, (
        f"Core document '{core_doc_seed.title}' appeared in the LLM prompt — it should be excluded"
    )
    assert non_core_seed.title in prompt_content, (
        f"Non-core document '{non_core_seed.title}' should appear in the LLM prompt"
    )


def test_load_knowledge_logs_loaded_document_counts_and_titles(
    monkeypatch: pytest.MonkeyPatch,
    ctx: CodegenContext,
):
    import app.services.nodes.load_knowledge as knowledge_module

    selected = next(
        entry for entry in REGISTRY_BY_ID.values()
        if entry.title == "Equation Template"
    )
    ctx.selected_titles = [selected.title]
    ctx.candidates_by_title = {selected.title: selected}
    logs = []
    monkeypatch.setattr(knowledge_module.logger, "info", logs.append)

    result = knowledge_module.make_load_knowledge_node(ctx)({})

    loaded_log = next(log for log in logs if log.event == "Selected skill documents loaded")
    assert loaded_log.context == {
        "core_count": len(CORE_DOCUMENTS),
        "selected_count": 1,
        "selected_titles": ["Equation Template"],
    }
    assert len(result["messages"]) == 3
