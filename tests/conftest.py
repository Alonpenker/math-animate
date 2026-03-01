import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

# Ensure settings can load during module imports in tests.
os.environ.setdefault("api_key", "test-api-key")
os.environ.setdefault("storage_endpoint", "localhost:9000")
os.environ.setdefault("storage_access_key", "minioadmin")
os.environ.setdefault("storage_secret_key", "minioadmin")
os.environ.setdefault("storage_bucket", "test-bucket")
os.environ.setdefault("database_url", "postgresql://manim:manim@localhost:5432/manim")
os.environ.setdefault("broker_url", "redis://localhost:6379/0")
os.environ.setdefault("backend_url", "redis://localhost:6379/1")
os.environ.setdefault("ollama_base_url", "http://localhost:11434")


@pytest.fixture
def test_store() -> dict[str, Any]:
    return {
        "jobs": {},
        "plans": {},
        "artifacts": {},
        "objects": {},
        "knowledge": {},
        "token_ledger": [],
        "worker_runner_calls": [],
        "render_delay_payloads": [],
        "status_updates": [],
        "subprocess_commands": [],
    }


@pytest.fixture
def fake_cursor() -> object:
    return object()


@pytest.fixture
def sample_user_request():
    from app.schemas.user_request import UserRequest

    return UserRequest(
        topic="Solving one-step linear equations",
        misconceptions=["Variables are labels, not numbers"],
        constraints=["Keep scenes short"],
        examples=["x + 3 = 7"],
        number_of_scenes=2,
    )


@pytest.fixture
def sample_video_plan():
    from app.schemas.scene_plan import ScenePlan
    from app.schemas.video_plan import VideoPlan

    return VideoPlan(
        scenes=[
            ScenePlan(
                learning_objective="Identify the variable in a linear equation.",
                visual_storyboard="Show x + 3 = 7 and highlight x.",
                voice_notes="The variable is the unknown value we solve for.",
                scene_number=1,
            ),
            ScenePlan(
                learning_objective="Isolate the variable with inverse operations.",
                visual_storyboard="Subtract 3 from both sides.",
                voice_notes="Apply the same operation to both sides to keep balance.",
                scene_number=2,
            ),
        ]
    )


@pytest.fixture
def mock_repositories(monkeypatch: pytest.MonkeyPatch, test_store: dict[str, Any]) -> None:
    from app.repositories.artifacts_repository import ArtifactsRepository
    from app.repositories.jobs_repository import JobsRepository
    from app.repositories.plans_repository import PlansRepository
    from app.schemas.artifact import Artifact
    from app.schemas.jobs import Job
    from app.schemas.plan import Plan

    def create_job(cursor: object, job: Job) -> None:
        test_store["jobs"][job.job_id] = job.model_copy(deep=True)

    def get_job(cursor: object, job_id):
        job = test_store["jobs"].get(job_id)
        return None if job is None else job.model_copy(deep=True)

    def update_job_status(cursor: object, job_id, status) -> None:
        existing = test_store["jobs"].get(job_id)
        if existing is None:
            updated = Job(job_id=job_id, status=status)
        else:
            updated = existing.model_copy(update={"status": status}, deep=True)
        test_store["jobs"][job_id] = updated
        test_store["status_updates"].append((job_id, status))

    def create_plan(cursor: object, job_id, plan) -> None:
        test_store["plans"][job_id] = Plan(
            job_id=job_id,
            plan=plan,
            approved=False,
        )

    def get_plan(cursor: object, job_id):
        plan = test_store["plans"].get(job_id)
        return None if plan is None else plan.model_copy(deep=True)

    def approve_plan(cursor: object, job_id, approved: bool = True):
        plan = test_store["plans"].get(job_id)
        if plan is None:
            return None
        updated = plan.model_copy(update={"approved": approved}, deep=True)
        test_store["plans"][job_id] = updated
        return updated.model_copy(deep=True)

    def create_artifact(cursor: object, artifact: Artifact) -> None:
        test_store["artifacts"][artifact.artifact_id] = artifact.model_copy(deep=True)

    def get_artifacts(cursor: object, job_id):
        return [
            artifact.model_copy(deep=True)
            for artifact in test_store["artifacts"].values()
            if artifact.job_id == job_id
        ]

    def get_artifact_by_id(cursor: object, artifact_id):
        artifact = test_store["artifacts"].get(artifact_id)
        return None if artifact is None else artifact.model_copy(deep=True)

    def get_all_artifacts(cursor: object, artifact_type=None, job_id=None):
        results = []
        for artifact in test_store["artifacts"].values():
            if artifact_type is not None and artifact.artifact_type != artifact_type:
                continue
            if job_id is not None and artifact.job_id != job_id:
                continue
            results.append(artifact.model_copy(deep=True))
        return results

    def delete_artifact(cursor: object, artifact_id):
        return test_store["artifacts"].pop(artifact_id, None) is not None

    monkeypatch.setattr(JobsRepository, "create_job", staticmethod(create_job))
    monkeypatch.setattr(JobsRepository, "get_job", staticmethod(get_job))
    monkeypatch.setattr(JobsRepository, "update_job_status", staticmethod(update_job_status))
    monkeypatch.setattr(PlansRepository, "create_plan", staticmethod(create_plan))
    monkeypatch.setattr(PlansRepository, "get_plan", staticmethod(get_plan))
    monkeypatch.setattr(PlansRepository, "approve_plan", staticmethod(approve_plan))
    monkeypatch.setattr(ArtifactsRepository, "create_artifact", staticmethod(create_artifact))
    monkeypatch.setattr(ArtifactsRepository, "get_artifacts", staticmethod(get_artifacts))
    monkeypatch.setattr(ArtifactsRepository, "get_artifact_by_id", staticmethod(get_artifact_by_id))
    monkeypatch.setattr(ArtifactsRepository, "get_all_artifacts", staticmethod(get_all_artifacts))
    monkeypatch.setattr(ArtifactsRepository, "delete_artifact", staticmethod(delete_artifact))


@pytest.fixture
def jobs_routes_with_runner_mock(
    monkeypatch: pytest.MonkeyPatch,
    mock_repositories: None,
    test_store: dict[str, Any],
):
    from app.routes import jobs as jobs_routes

    def fake_advance(job_request) -> None:
        test_store["worker_runner_calls"].append(job_request)

    monkeypatch.setattr(jobs_routes.WorkerRunner, "advance", staticmethod(fake_advance))
    return jobs_routes


@pytest.fixture
def mock_storage_service(test_store: dict[str, Any]):
    from app.services.files_storage_service import FilesStorageService

    class FakeFilesStorageService:
        def download_artifact(self, object_name: str, file_path: str) -> None:
            target = Path(file_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            data = test_store["objects"].get(object_name, b"fake-content")
            target.write_bytes(data)

        def delete_artifact(self, object_name: str) -> None:
            test_store["objects"].pop(object_name, None)

    return FakeFilesStorageService()


@pytest.fixture
def artifacts_routes_with_mocks(
    monkeypatch: pytest.MonkeyPatch,
    mock_repositories: None,
    mock_storage_service,
):
    from app.routes import artifacts as artifacts_routes
    return artifacts_routes


@pytest.fixture
def mock_worker_cursor(monkeypatch: pytest.MonkeyPatch, fake_cursor: object) -> None:
    from app.workers import worker as worker_module
    from app.workers import worker_helpers

    @contextmanager
    def cursor_context():
        yield fake_cursor

    # Patch in both modules: worker.py owns the inline PLANNED transition cursor;
    # worker_helpers.py owns all helper-function cursors.
    monkeypatch.setattr(worker_module, "get_worker_cursor", cursor_context)
    monkeypatch.setattr(worker_helpers, "get_worker_cursor", cursor_context)
    # current_task is only imported in worker_helpers (log_context lives there)
    monkeypatch.setattr(worker_helpers, "current_task", None)


@pytest.fixture
def mock_worker_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    from app.workers import worker as worker_module

    artifacts_root = tmp_path / "job_artifacts"
    render_root = tmp_path / "render_root"
    artifacts_root.mkdir(parents=True, exist_ok=True)
    render_root.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(worker_module.PathNames, "ARTIFACTS_FOLDER", str(artifacts_root))
    monkeypatch.setattr(worker_module.PathNames, "TMP_RENDER_FOLDER", str(render_root))
    return {"artifacts_root": artifacts_root, "render_root": render_root}


@pytest.fixture
def mock_worker_storage(monkeypatch: pytest.MonkeyPatch, test_store: dict[str, Any]) -> None:
    from app.workers import worker_helpers

    class FakeStorageService:
        def __init__(self, client: Any = None, bucket: str = "") -> None:
            pass

        def save_artifact(self, job_id, file_path: Path) -> str:
            path = Path(file_path)
            object_name = f"{job_id}/{path.name}"
            test_store["objects"][object_name] = path.read_bytes()
            return object_name

        def download_artifact(self, object_name: str, file_path: str) -> None:
            target = Path(file_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(test_store["objects"][object_name])

    # get_storage() and save_artifact_to_storage() live in worker_helpers,
    # so patch the names there (not in worker.py which re-exports them).
    monkeypatch.setattr(worker_helpers, "FilesStorageService", FakeStorageService)
    monkeypatch.setattr(worker_helpers, "get_storage_client", lambda: object())


@pytest.fixture
def mock_worker_verify_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patches verify_code in worker to always pass (return no failures)."""
    from app.workers import worker as worker_module

    monkeypatch.setattr(worker_module, "verify_code", lambda code: [])


@pytest.fixture
def mock_worker_llm(monkeypatch: pytest.MonkeyPatch, sample_video_plan) -> None:
    from app.workers import worker as worker_module

    fake_code = (
        "from manim import *\n\n"
        "class Scene1(Scene):\n"
        "    def construct(self):\n"
        "        self.wait()\n"
    )

    def fake_render_plan_prompt(user_request):
        return "fake-system-prompt", "fake-user-query"

    def fake_render_codegen_prompt(plan):
        return "fake-system-prompt", "fake-user-query"

    def fake_plan_call(system_prompt, user_query):
        return sample_video_plan, 100

    def fake_codegen_call(system_prompt, user_query):
        return fake_code, 200

    monkeypatch.setattr(worker_module.LLMService, "render_plan_prompt", staticmethod(fake_render_plan_prompt))
    monkeypatch.setattr(worker_module.LLMService, "render_codegen_prompt", staticmethod(fake_render_codegen_prompt))
    monkeypatch.setattr(worker_module.LLMService, "plan_call", staticmethod(fake_plan_call))
    monkeypatch.setattr(worker_module.LLMService, "codegen_call", staticmethod(fake_codegen_call))


@pytest.fixture
def mock_worker_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    # BudgetService is only imported in worker_helpers (via reserve_budget etc.)
    from app.workers import worker_helpers

    def fake_reserve(cursor, call_id, job_id, stage, provider, model, prompt_text):
        return 1000

    def fake_reconcile(cursor, call_id, consumed_tokens):
        pass

    def fake_release_on_error(cursor, call_id, reserved_tokens):
        pass

    monkeypatch.setattr(worker_helpers.BudgetService, "reserve", staticmethod(fake_reserve))
    monkeypatch.setattr(worker_helpers.BudgetService, "reconcile", staticmethod(fake_reconcile))
    monkeypatch.setattr(worker_helpers.BudgetService, "release_on_error", staticmethod(fake_release_on_error))


@pytest.fixture
def capture_render_delay(monkeypatch: pytest.MonkeyPatch, test_store: dict[str, Any]) -> None:
    from app.workers import worker as worker_module

    def fake_delay(payload: dict[str, Any]) -> None:
        test_store["render_delay_payloads"].append(payload)

    monkeypatch.setattr(worker_module.generate_render, "delay", fake_delay)


@pytest.fixture
def mock_rag_service(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import rag_service as rag_module
    import numpy as np

    monkeypatch.setattr(
        rag_module.RAGService, "embed_text",
        staticmethod(lambda text: np.zeros(1536, dtype=np.float32)),
    )


@pytest.fixture
def mock_knowledge_repository(monkeypatch: pytest.MonkeyPatch, test_store: dict[str, Any]) -> None:
    from app.repositories.knowledge_repository import KnowledgeRepository
    from app.schemas.knowledge import KnowledgeDocument, KnowledgeDocumentSchema, KnowledgeType

    S = KnowledgeDocumentSchema

    def create_document(cursor, document_id, content, doc_type, title, embedding):
        test_store["knowledge"][document_id] = {
            S.DOCUMENT_ID.name: document_id,
            S.CONTENT.name: content,
            S.DOC_TYPE.name: doc_type,
            S.TITLE.name: title,
            S.EMBEDDING.name: embedding,
        }

    def get_document(cursor, document_id):
        row = test_store["knowledge"].get(document_id)
        if row is None:
            return None
        return KnowledgeDocument(
            document_id=row[S.DOCUMENT_ID.name],
            content=row[S.CONTENT.name],
            doc_type=KnowledgeType(row[S.DOC_TYPE.name]),
            title=row[S.TITLE.name],
        )

    def delete_document(cursor, document_id):
        return test_store["knowledge"].pop(document_id, None) is not None
    
    def get_documents(cursor, doc_type):
        docs = []
        for row in test_store["knowledge"].values():
            if row[S.DOC_TYPE.name] != doc_type:
                continue
            docs.append(
                KnowledgeDocument(
                    document_id=row[S.DOCUMENT_ID.name],
                    content=row[S.CONTENT.name],
                    doc_type=KnowledgeType(row[S.DOC_TYPE.name]),
                    title=row[S.TITLE.name],
                )
            )
        return docs

    def search_similar(cursor, embedding, doc_type, limit=3):
        docs = []
        for row in test_store["knowledge"].values():
            if row[S.DOC_TYPE.name] != doc_type:
                continue
            docs.append(KnowledgeDocument(
                document_id=row[S.DOCUMENT_ID.name],
                content=row[S.CONTENT.name],
                doc_type=KnowledgeType(row[S.DOC_TYPE.name]),
                title=row[S.TITLE.name],
            ))
        return docs[:limit]

    monkeypatch.setattr(KnowledgeRepository, "create_document", staticmethod(create_document))
    monkeypatch.setattr(KnowledgeRepository, "get_document", staticmethod(get_document))
    monkeypatch.setattr(KnowledgeRepository, "get_documents", staticmethod(get_documents))
    monkeypatch.setattr(KnowledgeRepository, "delete_document", staticmethod(delete_document))
    monkeypatch.setattr(KnowledgeRepository, "search_similar", staticmethod(search_similar))


@pytest.fixture
def knowledge_routes_with_mocks(
    monkeypatch: pytest.MonkeyPatch,
    mock_knowledge_repository: None,
    mock_rag_service: None,
):
    from app.routes import knowledge as knowledge_routes
    return knowledge_routes


@pytest.fixture
def mock_token_ledger_repository(
    monkeypatch: pytest.MonkeyPatch,
    test_store: dict[str, Any],
) -> None:
    from datetime import date as date_type, timezone, datetime as dt

    from app.configs.llm_settings import DAILY_TOKEN_LIMIT, SOFT_THRESHOLD_RATIO
    from app.repositories.token_repository import TokenLedgerRepository
    from app.schemas.token_usage import BreakdownEntry, DailySummary

    def get_daily_summary(cursor, day: date_type):
        rows = [
            r for r in test_store["token_ledger"]
            if r["day"] == day
        ]

        breakdown = []
        total_consumed = 0
        total_reserved = 0

        groups: dict[tuple, dict] = {}
        for row in rows:
            key = (row["provider"], row["model"], row["stage"])
            if key not in groups:
                groups[key] = {"consumed": 0, "reserved": 0}
            if row["state"] == "RELEASED":
                groups[key]["consumed"] += row["consumed_tokens"]
            if row["state"] == "ACTIVE":
                groups[key]["reserved"] += row["reserved_tokens"]

        for (provider, model, stage), totals in groups.items():
            breakdown.append(BreakdownEntry(
                provider=provider,
                model=model,
                stage=stage,
                consumed=totals["consumed"],
                reserved=totals["reserved"],
            ))
            total_consumed += totals["consumed"]
            total_reserved += totals["reserved"]

        used = total_consumed + total_reserved
        remaining = max(0, DAILY_TOKEN_LIMIT - used)
        remaining_pct = round((remaining / DAILY_TOKEN_LIMIT) * 100, 2) if DAILY_TOKEN_LIMIT > 0 else 0.0
        soft_threshold = int(DAILY_TOKEN_LIMIT * SOFT_THRESHOLD_RATIO)

        return DailySummary(
            daily_limit=DAILY_TOKEN_LIMIT,
            consumed=total_consumed,
            reserved=total_reserved,
            remaining=remaining,
            remaining_pct=remaining_pct,
            soft_threshold_exceeded=used >= soft_threshold,
            breakdown=breakdown,
        )

    monkeypatch.setattr(
        TokenLedgerRepository, "get_daily_summary",
        staticmethod(get_daily_summary),
    )


@pytest.fixture
def usage_routes_with_mocks(
    monkeypatch: pytest.MonkeyPatch,
    mock_token_ledger_repository: None,
):
    from app.routes import usage as usage_routes
    return usage_routes
