from contextlib import contextmanager
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.configs.llm_settings import OPENROUTER_MODELS
from app.domain.job_state import JobStatus
from app.exceptions.llm_call_exception import LLMCallException
from app.exceptions.llm_usage_exception import LLMUsageException
from app.exceptions.quota_exceeded_error import QuotaExceededError
from app.schemas.jobs import Job, JobPlanRequest
from app.schemas.scene_plan import ScenePlan
from app.schemas.video_plan import VideoPlan
from app.schemas.user_request import UserRequest
from app.services.agent_service import AgentService, LangGraphCodegenState, NodesNames, _route_after_verify
from app.services.openrouter_service import OpenRouterTokenUsage


@contextmanager
def _cursor_ctx():
    yield object()


@pytest.fixture
def sample_user_request():
    return UserRequest(
        topic="Solving equations",
        misconceptions=[],
        constraints=[],
        examples=[],
        number_of_scenes=1,
    )


@pytest.fixture
def sample_video_plan_for_codegen():
    return VideoPlan(
        scenes=[
            ScenePlan(
                learning_objective="Learn equations",
                visual_storyboard="Show equation on screen",
                voice_notes="An equation has two sides",
                scene_number=1,
            ),
        ]
    )


@pytest.fixture
def sample_job_plan_request(sample_video_plan_for_codegen, sample_user_request):
    job = Job(job_id=uuid4(), status=JobStatus.PLANNED)
    return JobPlanRequest(
        job=job,
        plan=sample_video_plan_for_codegen,
        user_request=sample_user_request,
    )


# ---------------------------------------------------------------------------
# NodesNames enum
# ---------------------------------------------------------------------------

def test_nodes_names_enum_has_all_expected_values():
    assert NodesNames.DOCUMENT_SELECTION.value == "document_selection"
    assert NodesNames.LOAD_SELECTED_DOCUMENTS.value == "load_selected_documents"
    assert NodesNames.GENERATE_CODE_PLAN.value == "generate_code_plan"
    assert NodesNames.GENERATE_CODE.value == "generate_code"
    assert NodesNames.VERIFY.value == "verify"
    assert NodesNames.FIX_CODE.value == "fix_code"
    assert NodesNames.SAVE_AND_RENDER.value == "save_and_render"
    assert NodesNames.FAIL.value == "fail"


def test_nodes_names_non_loop_nodes_returns_correct_set():
    non_loop = NodesNames.non_loop_nodes()

    assert len(non_loop) == 7
    assert NodesNames.DOCUMENT_SELECTION in non_loop
    assert NodesNames.LOAD_SELECTED_DOCUMENTS in non_loop
    assert NodesNames.GENERATE_CODE_PLAN in non_loop
    assert NodesNames.GENERATE_CODE in non_loop
    assert NodesNames.VERIFY in non_loop
    assert NodesNames.SAVE_AND_RENDER in non_loop
    assert NodesNames.FAIL in non_loop
    assert NodesNames.FIX_CODE not in non_loop


def test_nodes_names_loop_nodes_returns_only_fix_and_verify():
    loop_nodes = NodesNames.loop_nodes_per_fix_attempt()

    assert len(loop_nodes) == 2
    assert NodesNames.FIX_CODE in loop_nodes
    assert NodesNames.VERIFY in loop_nodes


def _make_state(
    verification_failure: str = "",
    verification_fixable: bool = True,
    fix_attempt: int = 0,
) -> LangGraphCodegenState:
    from app.workers.worker_settings import MAX_FIX_ATTEMPTS
    return {
        "job_id": uuid4(),
        "plan": None,
        "user_request": None,
        "messages": [],
        "code": "",
        "code_plan": None,
        "referenced_templates": [],
        "verification_failure": verification_failure,
        "fix_attempt": fix_attempt,
        "verification_fixable": verification_fixable,
    }


def test_route_after_verify_routes_to_save_when_no_failure():
    state = _make_state(verification_failure="")
    assert _route_after_verify(state) == NodesNames.SAVE_AND_RENDER


def test_route_after_verify_routes_to_fail_when_not_fixable():
    state = _make_state(verification_failure="some error", verification_fixable=False)
    assert _route_after_verify(state) == NodesNames.FAIL


def test_route_after_verify_routes_to_fix_when_fixable_and_attempts_not_exhausted():
    from app.workers.worker_settings import MAX_FIX_ATTEMPTS
    state = _make_state(
        verification_failure="some error",
        verification_fixable=True,
        fix_attempt=MAX_FIX_ATTEMPTS - 1,
    )
    assert _route_after_verify(state) == NodesNames.FIX_CODE


def test_route_after_verify_routes_to_fail_when_fix_attempts_exhausted():
    from app.workers.worker_settings import MAX_FIX_ATTEMPTS
    state = _make_state(
        verification_failure="some error",
        verification_fixable=True,
        fix_attempt=MAX_FIX_ATTEMPTS,
    )
    assert _route_after_verify(state) == NodesNames.FAIL



def _make_stub_node_factories(ctx_module, fake_transition, extra_stubs: dict | None = None):
    """Return a dict of node factory stubs. Each stub simulates the transitions
    that the real node would make via ctx.set_status()."""
    import app.services.agent_service as agent_module

    def make_noop(ctx):
        def node(state): return {}
        return node

    defaults = {
        "make_document_selection_node": make_noop,
        "make_load_knowledge_node": lambda ctx: (lambda state: {"messages": []}),
        "make_code_plan_node": make_noop,
        "make_codegen_node": make_noop,
        "make_verify_node": make_noop,
        "make_fix_node": make_noop,
        "make_save_render_node": make_noop,
        "make_fail_node": make_noop,
    }
    if extra_stubs:
        defaults.update(extra_stubs)
    return defaults



def test_run_codegen_transitions_planned_to_codegen(
    monkeypatch: pytest.MonkeyPatch,
    sample_job_plan_request,
):
    """PLANNED → CODEGEN transition happens before the graph runs."""
    import app.services.agent_service as agent_module
    import app.services.nodes._context as ctx_module

    status_transitions = []

    def fake_transition(job_id, from_status, to_status):
        status_transitions.append((from_status, to_status))

    monkeypatch.setattr(agent_module, "transition_job", fake_transition)
    monkeypatch.setattr(ctx_module, "transition_job", fake_transition)

    stubs = _make_stub_node_factories(ctx_module, fake_transition)
    for attr, factory in stubs.items():
        monkeypatch.setattr(agent_module, attr, factory)

    AgentService.run_codegen(sample_job_plan_request)

    assert (JobStatus.PLANNED, JobStatus.CODEGEN) in status_transitions


def test_run_codegen_transitions_codegen_to_coded(
    monkeypatch: pytest.MonkeyPatch,
    sample_job_plan_request,
):
    """CODEGEN → CODED transition happens via the codegen node."""
    import app.services.agent_service as agent_module
    import app.services.nodes._context as ctx_module

    status_transitions = []

    def fake_transition(job_id, from_status, to_status):
        status_transitions.append((from_status, to_status))

    monkeypatch.setattr(agent_module, "transition_job", fake_transition)
    monkeypatch.setattr(ctx_module, "transition_job", fake_transition)

    def make_codegen_stub(ctx):
        def node(state):
            ctx.set_status(JobStatus.CODEGEN, JobStatus.CODED)
            return {"code": "from manim import *\n"}
        return node

    stubs = _make_stub_node_factories(ctx_module, fake_transition)
    stubs["make_codegen_node"] = make_codegen_stub
    for attr, factory in stubs.items():
        monkeypatch.setattr(agent_module, attr, factory)

    AgentService.run_codegen(sample_job_plan_request)

    assert (JobStatus.CODEGEN, JobStatus.CODED) in status_transitions


def test_run_codegen_initializes_langgraph_state_correctly(
    monkeypatch: pytest.MonkeyPatch,
    sample_job_plan_request,
):
    """The initial state passed to the compiled graph has the right fields."""
    import app.services.agent_service as agent_module
    import app.services.nodes._context as ctx_module
    from langgraph.graph import StateGraph

    captured_initial_state: dict = {}

    def fake_transition(job_id, from_status, to_status):
        pass

    monkeypatch.setattr(agent_module, "transition_job", fake_transition)
    monkeypatch.setattr(ctx_module, "transition_job", fake_transition)

    class FakeCompiledGraph:
        def invoke(self, state, config=None):
            captured_initial_state.update(state)

    monkeypatch.setattr(StateGraph, "__init__", lambda self, state_type: None)
    monkeypatch.setattr(StateGraph, "add_node", lambda self, *args: None)
    monkeypatch.setattr(StateGraph, "set_entry_point", lambda self, *args: None)
    monkeypatch.setattr(StateGraph, "add_edge", lambda self, *args: None)
    monkeypatch.setattr(StateGraph, "add_conditional_edges", lambda self, *args: None)
    monkeypatch.setattr(StateGraph, "compile", lambda self: FakeCompiledGraph())

    stubs = _make_stub_node_factories(ctx_module, fake_transition)
    for attr, factory in stubs.items():
        monkeypatch.setattr(agent_module, attr, factory)

    AgentService.run_codegen(sample_job_plan_request)

    assert captured_initial_state["job_id"] == sample_job_plan_request.job.job_id
    assert captured_initial_state["plan"] == sample_job_plan_request.plan
    assert captured_initial_state["user_request"] == sample_job_plan_request.user_request
    assert captured_initial_state["messages"] == []
    assert captured_initial_state["code"] == ""
    assert captured_initial_state["code_plan"] is None
    assert captured_initial_state["referenced_templates"] == []
    assert captured_initial_state["verification_failure"] == ""
    assert captured_initial_state["fix_attempt"] == 0
    assert captured_initial_state["verification_fixable"] is True


def test_run_codegen_handles_quota_exceeded_error(
    monkeypatch: pytest.MonkeyPatch,
    sample_job_plan_request,
):
    import app.services.agent_service as agent_module
    import app.services.nodes._context as ctx_module

    status_transitions = []

    def fake_transition(job_id, from_status, to_status):
        status_transitions.append((from_status, to_status))

    monkeypatch.setattr(agent_module, "transition_job", fake_transition)
    monkeypatch.setattr(ctx_module, "transition_job", fake_transition)

    def make_failing_node(ctx):
        def node(state):
            raise QuotaExceededError(limit=100, consumed=100, reserved=0, requested=1)
        return node

    monkeypatch.setattr(agent_module, "make_document_selection_node", make_failing_node)

    stubs = _make_stub_node_factories(ctx_module, fake_transition)
    for attr, factory in stubs.items():
        if attr != "make_document_selection_node":
            monkeypatch.setattr(agent_module, attr, factory)

    with pytest.raises(QuotaExceededError):
        AgentService.run_codegen(sample_job_plan_request)

    assert (JobStatus.PLANNED, JobStatus.CODEGEN) in status_transitions
    assert (JobStatus.CODEGEN, JobStatus.FAILED_QUOTA_EXCEEDED) in status_transitions


def test_run_codegen_handles_llm_usage_exception(
    monkeypatch: pytest.MonkeyPatch,
    sample_job_plan_request,
):
    import app.services.agent_service as agent_module
    import app.services.nodes._context as ctx_module

    status_transitions = []

    def fake_transition(job_id, from_status, to_status):
        status_transitions.append((from_status, to_status))

    monkeypatch.setattr(agent_module, "transition_job", fake_transition)
    monkeypatch.setattr(ctx_module, "transition_job", fake_transition)

    def make_failing_node(ctx):
        def node(state):
            raise LLMUsageException("Invalid output", total_tokens=100)
        return node

    monkeypatch.setattr(agent_module, "make_document_selection_node", make_failing_node)

    stubs = _make_stub_node_factories(ctx_module, fake_transition)
    for attr, factory in stubs.items():
        if attr != "make_document_selection_node":
            monkeypatch.setattr(agent_module, attr, factory)

    with pytest.raises(LLMUsageException):
        AgentService.run_codegen(sample_job_plan_request)

    assert (JobStatus.PLANNED, JobStatus.CODEGEN) in status_transitions
    assert (JobStatus.CODEGEN, JobStatus.FAILED_LLM_USAGE) in status_transitions


def test_run_codegen_handles_llm_call_exception_during_codegen(
    monkeypatch: pytest.MonkeyPatch,
    sample_job_plan_request,
):
    # Given — LLMCallException raised while ctx.current_status is CODEGEN
    import app.services.agent_service as agent_module
    import app.services.nodes._context as ctx_module

    status_transitions = []

    def fake_transition(job_id, from_status, to_status):
        status_transitions.append((from_status, to_status))

    monkeypatch.setattr(agent_module, "transition_job", fake_transition)
    monkeypatch.setattr(ctx_module, "transition_job", fake_transition)

    def make_failing_node(ctx):
        def node(state):
            raise LLMCallException("provider unavailable", total_tokens=0)
        return node

    monkeypatch.setattr(agent_module, "make_document_selection_node", make_failing_node)

    stubs = _make_stub_node_factories(ctx_module, fake_transition)
    for attr, factory in stubs.items():
        if attr != "make_document_selection_node":
            monkeypatch.setattr(agent_module, attr, factory)

    # When / Then
    with pytest.raises(LLMCallException):
        AgentService.run_codegen(sample_job_plan_request)

    assert (JobStatus.PLANNED, JobStatus.CODEGEN) in status_transitions
    assert (JobStatus.CODEGEN, JobStatus.FAILED_LLM_CALL) in status_transitions


def test_run_codegen_handles_llm_call_exception_during_fixing(
    monkeypatch: pytest.MonkeyPatch,
    sample_job_plan_request,
):
    # Given — LLMCallException raised while ctx.current_status is FIXING
    import app.services.agent_service as agent_module
    import app.services.nodes._context as ctx_module

    status_transitions = []

    def fake_transition(job_id, from_status, to_status):
        status_transitions.append((from_status, to_status))

    monkeypatch.setattr(agent_module, "transition_job", fake_transition)
    monkeypatch.setattr(ctx_module, "transition_job", fake_transition)

    # Codegen node advances ctx to CODED
    def make_codegen_stub(ctx):
        def node(state):
            ctx.set_status(JobStatus.CODEGEN, JobStatus.CODED)
            return {"code": "from manim import *\n"}
        return node

    # Verify node marks failure so router sends to FIX_CODE
    def make_verify_stub(ctx):
        def node(state):
            ctx.set_status(JobStatus.CODED, JobStatus.VERIFYING)
            return {"verification_failure": "bad code", "verification_fixable": True, "fix_attempt": 0}
        return node

    # Fix node advances ctx to FIXING then raises LLMCallException
    def make_fix_stub(ctx):
        def node(state):
            ctx.current_status = JobStatus.FIXING  # simulate the real fix node's status update
            raise LLMCallException("provider unavailable during fix", total_tokens=0)
        return node

    stubs = _make_stub_node_factories(ctx_module, fake_transition)
    stubs["make_codegen_node"] = make_codegen_stub
    stubs["make_verify_node"] = make_verify_stub
    stubs["make_fix_node"] = make_fix_stub
    for attr, factory in stubs.items():
        monkeypatch.setattr(agent_module, attr, factory)

    # When / Then
    with pytest.raises(LLMCallException):
        AgentService.run_codegen(sample_job_plan_request)

    assert (JobStatus.FIXING, JobStatus.FAILED_LLM_CALL) in status_transitions


def test_run_codegen_handles_generic_exception(
    monkeypatch: pytest.MonkeyPatch,
    sample_job_plan_request,
):
    import app.services.agent_service as agent_module
    import app.services.nodes._context as ctx_module

    status_transitions = []

    def fake_transition(job_id, from_status, to_status):
        status_transitions.append((from_status, to_status))

    monkeypatch.setattr(agent_module, "transition_job", fake_transition)
    monkeypatch.setattr(ctx_module, "transition_job", fake_transition)

    def make_failing_node(ctx):
        def node(state):
            raise RuntimeError("Unexpected error")
        return node

    monkeypatch.setattr(agent_module, "make_document_selection_node", make_failing_node)

    stubs = _make_stub_node_factories(ctx_module, fake_transition)
    for attr, factory in stubs.items():
        if attr != "make_document_selection_node":
            monkeypatch.setattr(agent_module, attr, factory)

    with pytest.raises(RuntimeError):
        AgentService.run_codegen(sample_job_plan_request)

    assert (JobStatus.PLANNED, JobStatus.CODEGEN) in status_transitions
    assert (JobStatus.CODEGEN, JobStatus.FAILED_CODEGEN) in status_transitions
