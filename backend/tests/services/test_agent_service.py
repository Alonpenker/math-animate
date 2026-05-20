from contextlib import contextmanager
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.configs.llm_settings import OPENROUTER_MODELS
from app.domain.job_state import JobStatus
from app.exceptions.llm_usage_exception import LLMUsageException
from app.exceptions.quota_exceeded_error import QuotaExceededError
from app.schemas.jobs import Job, JobPlanRequest
from app.schemas.video_plan import VideoPlan
from app.schemas.scene_plan import ScenePlan
from app.services.agent_service import AgentService, LangGraphCodegenState, NodesNames
from app.services.openrouter_service import CallType
from app.services.openrouter_service import OpenRouterTokenUsage


@contextmanager
def _cursor_ctx():
    yield object()


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
def sample_job_plan_request(sample_video_plan_for_codegen):
    job = Job(job_id=uuid4(), status=JobStatus.PLANNED)
    return JobPlanRequest(job=job, plan=sample_video_plan_for_codegen)


def test_run_codegen_transitions_job_through_codegen_status(monkeypatch: pytest.MonkeyPatch, sample_job_plan_request):
    # Given
    from app.services import agent_service as agent_module
    from app.workers import worker_helpers, worker as worker_module
    import tempfile

    status_transitions = []
    skill_retrieval_candidates = type('obj', (), {
        'all_candidates': []
    })()

    class FakeStorageService:
        pass

    class FakeGenerateRender:
        def delay(self, *args, **kwargs):
            pass

    def fake_transition(job_id, from_status, to_status):
        status_transitions.append((from_status, to_status))

    def fake_retrieve(cursor, plan_text):
        return skill_retrieval_candidates

    def fake_read_knowledge_file(path):
        return "# Core content"

    monkeypatch.setattr(agent_module, "transition_job", fake_transition)
    monkeypatch.setattr(agent_module, "get_worker_cursor", _cursor_ctx)
    monkeypatch.setattr(agent_module.SkillRetrievalService, "retrieve", staticmethod(fake_retrieve))
    monkeypatch.setattr(agent_module, "read_knowledge_file", fake_read_knowledge_file)
    monkeypatch.setattr(agent_module, "get_storage", lambda: FakeStorageService())
    monkeypatch.setattr(agent_module, "save_artifact_to_storage", lambda *args, **kwargs: None)

    # Mock OpenRouter calls
    def fake_openrouter_invoke_structured(**kwargs):
        from app.services.agent_service import SelectedSkillDocuments
        return SelectedSkillDocuments(selected_titles=[]), OpenRouterTokenUsage()

    def fake_openrouter_invoke(**kwargs):
        return AIMessage(content="from manim import *\nclass Scene(Scene): pass"), OpenRouterTokenUsage()

    monkeypatch.setattr(
        agent_module.OpenRouterService,
        "invoke_structured",
        staticmethod(fake_openrouter_invoke_structured),
    )
    monkeypatch.setattr(
        agent_module.OpenRouterService,
        "invoke",
        staticmethod(fake_openrouter_invoke),
    )

    # Mock worker helpers
    monkeypatch.setattr(worker_helpers, "verify_code", lambda code, path: None)
    monkeypatch.setattr(worker_helpers, "dry_run_docker", lambda code_path, media_dir: (True, "", True))
    monkeypatch.setattr(worker_helpers, "get_storage", lambda: FakeStorageService())
    monkeypatch.setattr(worker_helpers, "save_artifact_to_storage", lambda *args, **kwargs: None)

    # Mock celery task
    monkeypatch.setattr(worker_module, "generate_render", FakeGenerateRender())

    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(agent_module.PathNames, "TMP_RENDER_FOLDER", tmpdir)
        monkeypatch.setattr(agent_module.PathNames, "ARTIFACTS_FOLDER", tmpdir)

        # When
        AgentService.run_codegen(sample_job_plan_request)

    # Then
    assert (JobStatus.PLANNED, JobStatus.CODEGEN) in status_transitions
    assert (JobStatus.CODEGEN, JobStatus.CODED) in status_transitions


def test_nodes_names_enum_has_all_expected_values():
    # When / Then
    assert NodesNames.DOCUMENT_SELECTION.value == "document_selection"
    assert NodesNames.LOAD_SELECTED_DOCUMENTS.value == "load_selected_documents"
    assert NodesNames.GENERATE_CODE.value == "generate_code"
    assert NodesNames.VERIFY.value == "verify"
    assert NodesNames.FIX_CODE.value == "fix_code"
    assert NodesNames.SAVE_AND_RENDER.value == "save_and_render"
    assert NodesNames.FAIL.value == "fail"


def test_nodes_names_non_loop_nodes_returns_correct_set():
    # When
    non_loop = NodesNames.non_loop_nodes()

    # Then
    assert len(non_loop) == 6
    assert NodesNames.DOCUMENT_SELECTION in non_loop
    assert NodesNames.LOAD_SELECTED_DOCUMENTS in non_loop
    assert NodesNames.GENERATE_CODE in non_loop
    assert NodesNames.VERIFY in non_loop
    assert NodesNames.SAVE_AND_RENDER in non_loop
    assert NodesNames.FAIL in non_loop
    assert NodesNames.FIX_CODE not in non_loop


def test_nodes_names_loop_nodes_returns_only_fix_and_verify():
    # When
    loop_nodes = NodesNames.loop_nodes_per_fix_attempt()

    # Then
    assert len(loop_nodes) == 2
    assert NodesNames.FIX_CODE in loop_nodes
    assert NodesNames.VERIFY in loop_nodes


def test_run_codegen_handles_quota_exceeded_error(monkeypatch: pytest.MonkeyPatch, sample_job_plan_request):
    # Given
    from app.services import agent_service as agent_module

    status_transitions = []

    def fake_transition(job_id, from_status, to_status):
        status_transitions.append((from_status, to_status))

    def fake_retrieve(cursor, plan_text):
        raise QuotaExceededError(limit=100, consumed=100, reserved=0, requested=1)

    monkeypatch.setattr(agent_module, "transition_job", fake_transition)
    monkeypatch.setattr(agent_module, "get_worker_cursor", _cursor_ctx)
    monkeypatch.setattr(agent_module.SkillRetrievalService, "retrieve", staticmethod(fake_retrieve))

    # When / Then
    with pytest.raises(QuotaExceededError):
        AgentService.run_codegen(sample_job_plan_request)

    # Verify it transitioned to failed quota state
    assert (JobStatus.PLANNED, JobStatus.CODEGEN) in status_transitions
    assert (JobStatus.CODEGEN, JobStatus.FAILED_QUOTA_EXCEEDED) in status_transitions


def test_run_codegen_handles_llm_usage_exception(monkeypatch: pytest.MonkeyPatch, sample_job_plan_request):
    # Given
    from app.services import agent_service as agent_module

    status_transitions = []

    def fake_transition(job_id, from_status, to_status):
        status_transitions.append((from_status, to_status))

    def fake_retrieve(cursor, plan_text):
        raise LLMUsageException("Invalid output", total_tokens=100)

    monkeypatch.setattr(agent_module, "transition_job", fake_transition)
    monkeypatch.setattr(agent_module, "get_worker_cursor", _cursor_ctx)
    monkeypatch.setattr(agent_module.SkillRetrievalService, "retrieve", staticmethod(fake_retrieve))

    # When / Then
    with pytest.raises(LLMUsageException):
        AgentService.run_codegen(sample_job_plan_request)

    # Verify it transitioned to failed LLM usage state
    assert (JobStatus.CODEGEN, JobStatus.FAILED_LLM_USAGE) in status_transitions


def test_run_codegen_handles_generic_exception(monkeypatch: pytest.MonkeyPatch, sample_job_plan_request):
    # Given
    from app.services import agent_service as agent_module

    status_transitions = []

    def fake_transition(job_id, from_status, to_status):
        status_transitions.append((from_status, to_status))

    def fake_retrieve(cursor, plan_text):
        raise RuntimeError("Unexpected error")

    monkeypatch.setattr(agent_module, "transition_job", fake_transition)
    monkeypatch.setattr(agent_module, "get_worker_cursor", _cursor_ctx)
    monkeypatch.setattr(agent_module.SkillRetrievalService, "retrieve", staticmethod(fake_retrieve))

    # When / Then
    with pytest.raises(RuntimeError):
        AgentService.run_codegen(sample_job_plan_request)

    # Verify it transitioned to failed codegen state (because error happened during document selection)
    assert (JobStatus.CODEGEN, JobStatus.FAILED_CODEGEN) in status_transitions


def test_run_codegen_initializes_langgraph_state_correctly(monkeypatch: pytest.MonkeyPatch, sample_job_plan_request):
    # Given
    from app.services import agent_service as agent_module
    from app.workers import worker_helpers

    captured_initial_state = {}

    original_compile = None

    def fake_transition(job_id, from_status, to_status):
        pass

    class FakeCompiledGraph:
        def invoke(self, state, config=None):
            captured_initial_state.update(state)
            return None

    class FakeGraph:
        def add_node(self, name, func):
            pass

        def set_entry_point(self, name):
            pass

        def add_edge(self, from_node, to_node):
            pass

        def add_conditional_edges(self, from_node, func):
            pass

        def compile(self):
            return FakeCompiledGraph()

    class FakePath:
        def __init__(self, path_str):
            self.path_str = path_str

        def __truediv__(self, other):
            return FakePath(f"{self.path_str}/{other}")

        def mkdir(self, parents=False, exist_ok=False):
            pass

    def fake_retrieve(cursor, plan_text):
        return type('obj', (), {'all_candidates': []})()

    def fake_read_knowledge_file(path):
        return "content"

    def fake_openrouter_invoke_structured(**kwargs):
        from app.services.agent_service import SelectedSkillDocuments
        return SelectedSkillDocuments(selected_titles=[]), OpenRouterTokenUsage()

    monkeypatch.setattr(agent_module, "transition_job", fake_transition)
    monkeypatch.setattr(agent_module, "get_worker_cursor", _cursor_ctx)
    monkeypatch.setattr(agent_module.SkillRetrievalService, "retrieve", staticmethod(fake_retrieve))
    monkeypatch.setattr(agent_module, "read_knowledge_file", fake_read_knowledge_file)
    monkeypatch.setattr(agent_module, "Path", FakePath)
    monkeypatch.setattr(agent_module.StateGraph, "__init__", lambda self, state_type: None)
    monkeypatch.setattr(agent_module.StateGraph, "add_node", lambda self, *args: None)
    monkeypatch.setattr(agent_module.StateGraph, "set_entry_point", lambda self, *args: None)
    monkeypatch.setattr(agent_module.StateGraph, "add_edge", lambda self, *args: None)
    monkeypatch.setattr(agent_module.StateGraph, "add_conditional_edges", lambda self, *args: None)
    monkeypatch.setattr(agent_module.StateGraph, "compile", lambda self: FakeCompiledGraph())
    monkeypatch.setattr(
        agent_module.OpenRouterService,
        "invoke_structured",
        staticmethod(fake_openrouter_invoke_structured),
    )

    # When
    AgentService.run_codegen(sample_job_plan_request)

    # Then
    assert captured_initial_state["job_id"] == sample_job_plan_request.job.job_id
    assert captured_initial_state["plan"] == sample_job_plan_request.plan
    assert captured_initial_state["messages"] == []
    assert captured_initial_state["code"] == ""
    assert captured_initial_state["verification_failure"] == ""
    assert captured_initial_state["fix_attempt"] == 0
    assert captured_initial_state["verification_fixable"] is True


def test_route_after_verify_returns_save_and_render_when_no_failure(monkeypatch: pytest.MonkeyPatch, sample_job_plan_request):
    # Given - Setup minimal mocks for successful path
    from app.services import agent_service as agent_module
    from app.workers import worker_helpers, worker as worker_module
    import tempfile

    def fake_transition(job_id, from_status, to_status):
        pass

    class FakeGenerateRender:
        def delay(self, *args, **kwargs):
            pass

    def fake_retrieve(cursor, plan_text):
        return type('obj', (), {'all_candidates': []})()

    def fake_read_knowledge_file(path):
        return "content"

    def fake_openrouter_invoke_structured(**kwargs):
        from app.services.agent_service import SelectedSkillDocuments
        return SelectedSkillDocuments(selected_titles=[]), OpenRouterTokenUsage()

    def fake_openrouter_invoke(**kwargs):
        return AIMessage(content="from manim import *\nclass Scene(Scene): pass"), OpenRouterTokenUsage()

    monkeypatch.setattr(agent_module, "transition_job", fake_transition)
    monkeypatch.setattr(agent_module, "get_worker_cursor", _cursor_ctx)
    monkeypatch.setattr(agent_module.SkillRetrievalService, "retrieve", staticmethod(fake_retrieve))
    monkeypatch.setattr(agent_module, "read_knowledge_file", fake_read_knowledge_file)
    monkeypatch.setattr(agent_module, "get_storage", lambda: type('obj', (), {})())
    monkeypatch.setattr(agent_module, "save_artifact_to_storage", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        agent_module.OpenRouterService,
        "invoke_structured",
        staticmethod(fake_openrouter_invoke_structured),
    )
    monkeypatch.setattr(
        agent_module.OpenRouterService,
        "invoke",
        staticmethod(fake_openrouter_invoke),
    )
    monkeypatch.setattr(worker_helpers, "verify_code", lambda code, path: None)
    monkeypatch.setattr(worker_helpers, "dry_run_docker", lambda code_path, media_dir: (True, "", True))
    monkeypatch.setattr(worker_helpers, "get_storage", lambda: type('obj', (), {})())
    monkeypatch.setattr(worker_helpers, "save_artifact_to_storage", lambda *args, **kwargs: None)

    # Mock the generate_render import that happens inside node_save_and_render
    monkeypatch.setattr(worker_module, "generate_render", FakeGenerateRender())

    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(agent_module.PathNames, "TMP_RENDER_FOLDER", tmpdir)
        monkeypatch.setattr(agent_module.PathNames, "ARTIFACTS_FOLDER", tmpdir)

        # When - this should complete without raising
        try:
            AgentService.run_codegen(sample_job_plan_request)
            # If we get here, the routing worked correctly
            success = True
        except Exception as e:
            success = False
            raise

        # Then
        assert success
