import os
from typing import Any

import pytest

# Ensure settings can load during module imports across all test modules.
os.environ.setdefault("api_key", "test-api-key")
os.environ.setdefault("storage_endpoint", "localhost:9000")
os.environ.setdefault("storage_access_key", "minioadmin")
os.environ.setdefault("storage_secret_key", "minioadmin")
os.environ.setdefault("storage_bucket", "test-bucket")
os.environ.setdefault("database_url", "postgresql://manim:manim@localhost:5432/manim")
os.environ.setdefault("broker_url", "redis://localhost:6379/0")
os.environ.setdefault("backend_url", "redis://localhost:6379/1")
os.environ.setdefault("ollama_base_url", "http://localhost:11434")
os.environ.setdefault("redis_url", "redis://localhost:6379/0")


# ─────────────────────────────────────────────────────────────────────────────
# SHARED PRIMITIVES
# These fixtures are available to every test folder (routes/, workers/, etc.)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def test_store() -> dict[str, Any]:
    """
    In-memory store that replaces all persistent backends (DB, Redis, MinIO).
    Each key holds a different resource type so fixtures can share state cleanly.
    """
    return {
        "jobs": {},
        "plans": {},
        "artifacts": {},
        "objects": {},          # MinIO objects keyed by object_name
        "knowledge": {},
        "token_ledger": [],
        "worker_runner_calls": [],
        "render_delay_payloads": [],
        "status_updates": [],   # list of (job_id, JobStatus) tuples in order
        "subprocess_commands": [],
    }


@pytest.fixture
def fake_cursor() -> object:
    """
    Opaque placeholder cursor.
    All repository methods are patched in tests so the cursor value is never used
    for real — it just satisfies the dependency parameter signature.
    """
    return object()


@pytest.fixture
def sample_user_request():
    """Standard teacher lesson request used as input for planning tests."""
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
    """Two-scene video plan corresponding to sample_user_request."""
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


# ─────────────────────────────────────────────────────────────────────────────
# SHARED REPOSITORY MOCKS
# Used by both routes/ and workers/ — must live in the root conftest.
# All patched methods ignore their first argument (cursor or redis_client) so
# tests work without real DB or Redis connections.
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_repositories(monkeypatch: pytest.MonkeyPatch, test_store: dict[str, Any]) -> None:
    """
    Replaces every SQL and Redis repository method with an in-memory equivalent
    backed by test_store.  The first argument of each patched method is the
    connection/cursor — it is intentionally ignored here since no real I/O occurs.
    """
    from app.repositories.artifacts_repository import ArtifactsRepository
    from app.repositories.jobs_repository import JobsRepository
    from app.repositories.plans_repository import PlansRepository
    from app.schemas.artifact import Artifact
    from app.schemas.jobs import Job
    from app.schemas.plan import Plan

    # ── Jobs (Redis-backed in production) ───────────────────────────────────

    def create_job(_conn, job: Job) -> None:
        test_store["jobs"][job.job_id] = job.model_copy(deep=True)

    def get_job(_conn, job_id):
        job = test_store["jobs"].get(job_id)
        return None if job is None else job.model_copy(deep=True)

    def update_job_status(_conn, job_id, status) -> None:
        existing = test_store["jobs"].get(job_id)
        updated = (
            existing.model_copy(update={"status": status}, deep=True)
            if existing is not None
            else Job(job_id=job_id, status=status)
        )
        test_store["jobs"][job_id] = updated
        test_store["status_updates"].append((job_id, status))

    # ── Plans (cursor-backed in production) ─────────────────────────────────

    def create_plan(_cursor, job_id, plan) -> None:
        test_store["plans"][job_id] = Plan(job_id=job_id, plan=plan, approved=False)

    def get_plan(_cursor, job_id):
        plan = test_store["plans"].get(job_id)
        return None if plan is None else plan.model_copy(deep=True)

    def approve_plan(_cursor, job_id, approved: bool = True):
        plan = test_store["plans"].get(job_id)
        if plan is None:
            return None
        updated = plan.model_copy(update={"approved": approved}, deep=True)
        test_store["plans"][job_id] = updated
        return updated.model_copy(deep=True)

    # ── Artifacts (cursor-backed in production) ──────────────────────────────

    def create_artifact(_cursor, artifact: Artifact) -> None:
        test_store["artifacts"][artifact.artifact_id] = artifact.model_copy(deep=True)

    def get_artifacts(_cursor, job_id):
        return [
            a.model_copy(deep=True)
            for a in test_store["artifacts"].values()
            if a.job_id == job_id
        ]

    def get_artifact_by_id(_cursor, artifact_id):
        artifact = test_store["artifacts"].get(artifact_id)
        return None if artifact is None else artifact.model_copy(deep=True)

    def get_all_artifacts(_cursor, artifact_type=None, job_id=None):
        results = []
        for artifact in test_store["artifacts"].values():
            if artifact_type is not None and artifact.artifact_type != artifact_type:
                continue
            if job_id is not None and artifact.job_id != job_id:
                continue
            results.append(artifact.model_copy(deep=True))
        return results

    def delete_artifact(_cursor, artifact_id):
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
