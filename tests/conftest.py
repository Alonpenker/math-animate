import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

# Ensure settings can load during module imports in tests.
os.environ.setdefault("openai_key", "test-openai-key")
os.environ.setdefault("storage_endpoint", "localhost:9000")
os.environ.setdefault("storage_access_key", "minioadmin")
os.environ.setdefault("storage_secret_key", "minioadmin")
os.environ.setdefault("storage_bucket", "test-bucket")
os.environ.setdefault("database_url", "postgresql://manim:manim@localhost:5432/manim")
os.environ.setdefault("broker_url", "redis://localhost:6379/0")
os.environ.setdefault("backend_url", "redis://localhost:6379/1")


@pytest.fixture
def test_store() -> dict[str, Any]:
    return {
        "jobs": {},
        "plans": {},
        "artifacts": {},
        "objects": {},
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
            plan=plan.model_dump_json(),
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

    monkeypatch.setattr(JobsRepository, "create_job", staticmethod(create_job))
    monkeypatch.setattr(JobsRepository, "get_job", staticmethod(get_job))
    monkeypatch.setattr(JobsRepository, "update_job_status", staticmethod(update_job_status))
    monkeypatch.setattr(PlansRepository, "create_plan", staticmethod(create_plan))
    monkeypatch.setattr(PlansRepository, "get_plan", staticmethod(get_plan))
    monkeypatch.setattr(PlansRepository, "approve_plan", staticmethod(approve_plan))
    monkeypatch.setattr(ArtifactsRepository, "create_artifact", staticmethod(create_artifact))
    monkeypatch.setattr(ArtifactsRepository, "get_artifacts", staticmethod(get_artifacts))
    monkeypatch.setattr(ArtifactsRepository, "get_artifact_by_id", staticmethod(get_artifact_by_id))


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
def mock_worker_cursor(monkeypatch: pytest.MonkeyPatch, fake_cursor: object) -> None:
    from app.workers import worker as worker_module

    @contextmanager
    def cursor_context():
        yield fake_cursor

    monkeypatch.setattr(worker_module, "get_worker_cursor", cursor_context)
    monkeypatch.setattr(worker_module, "current_task", None)


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
    from app.workers import worker as worker_module

    class FakeStorageService:
        def __init__(self, client: Any, bucket: str):
            self._client = client
            self._bucket = bucket

        def save_artifact(self, job_id, file_path: Path) -> str:
            path = Path(file_path)
            object_name = f"{job_id}/{path.name}"
            test_store["objects"][object_name] = path.read_bytes()
            return object_name

        def download_artifact(self, object_name: str, file_path: str) -> None:
            target = Path(file_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(test_store["objects"][object_name])

    monkeypatch.setattr(worker_module, "FilesStorageService", FakeStorageService)
    monkeypatch.setattr(worker_module, "get_storage_client", lambda: object())


@pytest.fixture
def mock_worker_llm(monkeypatch: pytest.MonkeyPatch, sample_video_plan) -> None:
    from app.workers import worker as worker_module

    def fake_plan_call(user_request):
        return sample_video_plan

    def fake_codegen_call(plan) -> str:
        return (
            "from manim import *\n\n"
            "class Scene1(Scene):\n"
            "    def construct(self):\n"
            "        self.wait()\n"
        )

    monkeypatch.setattr(worker_module.LLMService, "plan_call", staticmethod(fake_plan_call))
    monkeypatch.setattr(worker_module.LLMService, "codegen_call", staticmethod(fake_codegen_call))


@pytest.fixture
def capture_render_delay(monkeypatch: pytest.MonkeyPatch, test_store: dict[str, Any]) -> None:
    from app.workers import worker as worker_module

    def fake_delay(payload: dict[str, Any]) -> None:
        test_store["render_delay_payloads"].append(payload)

    monkeypatch.setattr(worker_module.generate_render, "delay", fake_delay)
