import hashlib
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

from app.domain.job_state import JobStatus
from app.schemas.artifact import Artifact, ArtifactType
from app.schemas.jobs import Job, JobPlanRequest, JobRequest, JobUserRequest
from app.schemas.plan import Plan


# ---------------------------------------------------------------------------
# verify_code unit tests (no DB / storage / Celery)
# ---------------------------------------------------------------------------

def _make_mypy_pass(monkeypatch):
    """Patch subprocess.run so mypy always reports success."""
    from app.workers import worker_helpers

    def fake_mypy(cmd, *, capture_output, text, timeout):
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(worker_helpers.subprocess, "run", fake_mypy)


def test_verify_code_passes_valid_manim_code(monkeypatch):
    from app.workers.worker_helpers import verify_code

    _make_mypy_pass(monkeypatch)
    code = (
        "from manim import *\n\n"
        "class Scene1(Scene):\n"
        "    def construct(self):\n"
        "        self.wait()\n"
    )
    assert verify_code(code) == []


def test_verify_code_fails_on_mypy_errors(monkeypatch):
    from app.workers import worker_helpers
    from app.workers.worker_helpers import verify_code

    def fake_mypy_fail(cmd, *, capture_output, text, timeout):
        return subprocess.CompletedProcess(cmd, 1, "error: some type error\n", "")

    monkeypatch.setattr(worker_helpers.subprocess, "run", fake_mypy_fail)

    code = "from manim import *\n"
    failures = verify_code(code)
    assert any("mypy errors" in f for f in failures)


def test_verify_code_fails_on_forbidden_import(monkeypatch):
    from app.workers.worker_helpers import verify_code

    _make_mypy_pass(monkeypatch)
    code = "import os\nfrom manim import *\n"
    failures = verify_code(code)
    assert any("os" in f for f in failures)


def test_verify_code_fails_on_from_import_forbidden_module(monkeypatch):
    from app.workers.worker_helpers import verify_code

    _make_mypy_pass(monkeypatch)
    code = "from subprocess import run\nfrom manim import *\n"
    failures = verify_code(code)
    assert any("subprocess" in f for f in failures)


def test_verify_code_fails_on_dangerous_builtin_exec(monkeypatch):
    from app.workers.worker_helpers import verify_code

    _make_mypy_pass(monkeypatch)
    code = "from manim import *\nexec('print(1)')\n"
    failures = verify_code(code)
    assert any("exec" in f for f in failures)


def test_verify_code_fails_on_dangerous_builtin_eval(monkeypatch):
    from app.workers.worker_helpers import verify_code

    _make_mypy_pass(monkeypatch)
    code = "from manim import *\nx = eval('1+1')\n"
    failures = verify_code(code)
    assert any("eval" in f for f in failures)


def test_verify_code_fails_on_syntax_error(monkeypatch):
    from app.workers.worker_helpers import verify_code

    _make_mypy_pass(monkeypatch)
    code = "from manim import *\ndef broken(:\n"
    failures = verify_code(code)
    assert any("syntax error" in f.lower() for f in failures)


def test_verify_code_allows_all_permitted_imports(monkeypatch):
    from app.workers.worker_helpers import verify_code

    _make_mypy_pass(monkeypatch)
    code = (
        "import math\n"
        "import random\n"
        "import typing\n"
        "import numpy as np\n"
        "from manim import *\n"
        "from colour import Color\n"
    )
    assert verify_code(code) == []


def test_verify_code_accumulates_multiple_failures(monkeypatch):
    from app.workers.worker_helpers import verify_code

    _make_mypy_pass(monkeypatch)
    code = "import os\nimport sys\nexec('x')\n"
    failures = verify_code(code)
    # Should flag both forbidden imports and dangerous builtins
    combined = " ".join(failures)
    assert "os" in combined or "sys" in combined
    assert "exec" in combined


# ---------------------------------------------------------------------------
# generate_plan tests
# ---------------------------------------------------------------------------

def test_generate_plan_success_transitions_and_saves_plan(
    mock_repositories,
    mock_worker_cursor,
    mock_worker_llm,
    mock_worker_budget,
    sample_user_request,
    test_store,
):
    from app.workers import worker as worker_module

    job = Job(status=JobStatus.CREATED)
    test_store["jobs"][job.job_id] = job
    payload = JobUserRequest(job=job, user_request=sample_user_request).model_dump(mode="json")

    worker_module.generate_plan(payload)

    assert test_store["jobs"][job.job_id].status == JobStatus.PLANNED
    assert job.job_id in test_store["plans"]
    assert test_store["status_updates"][-2:] == [
        (job.job_id, JobStatus.PLANNING),
        (job.job_id, JobStatus.PLANNED),
    ]


def test_generate_plan_failure_sets_failed_planning(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_budget,
    sample_user_request,
    test_store,
):
    from app.workers import worker as worker_module

    def fake_render_plan_prompt(user_request):
        return "fake-system-prompt", "fake-user-query"

    def failing_plan_call(system_prompt, user_query):
        raise RuntimeError("planning failed")

    monkeypatch.setattr(worker_module.LLMService, "render_plan_prompt", staticmethod(fake_render_plan_prompt))
    monkeypatch.setattr(worker_module.LLMService, "plan_call", staticmethod(failing_plan_call))

    job = Job(status=JobStatus.CREATED)
    test_store["jobs"][job.job_id] = job
    payload = JobUserRequest(job=job, user_request=sample_user_request).model_dump(mode="json")

    with pytest.raises(RuntimeError, match="planning failed"):
        worker_module.generate_plan(payload)

    assert test_store["jobs"][job.job_id].status == JobStatus.FAILED_PLANNING
    assert test_store["status_updates"][-1] == (job.job_id, JobStatus.FAILED_PLANNING)


# ---------------------------------------------------------------------------
# generate_code tests
# ---------------------------------------------------------------------------

def test_generate_code_success_persists_python_artifact_and_enqueues_render(
    mock_repositories,
    mock_worker_cursor,
    mock_worker_paths,
    mock_worker_storage,
    mock_worker_llm,
    mock_worker_budget,
    mock_worker_verify_code,
    capture_render_delay,
    sample_video_plan,
    test_store,
):
    from app.workers import worker as worker_module

    job = Job(status=JobStatus.APPROVED)
    test_store["jobs"][job.job_id] = job
    payload = JobPlanRequest(job=job, plan=sample_video_plan).model_dump(mode="json")

    worker_module.generate_code(payload)

    assert test_store["jobs"][job.job_id].status == JobStatus.CODED
    assert test_store["status_updates"][-2:] == [
        (job.job_id, JobStatus.CODEGEN),
        (job.job_id, JobStatus.CODED),
    ]

    job_artifacts = [a for a in test_store["artifacts"].values() if a.job_id == job.job_id]
    assert len(job_artifacts) == 1
    artifact = job_artifacts[0]
    assert artifact.artifact_type == ArtifactType.PYTHON_FILE
    assert artifact.path in test_store["objects"]
    stored_bytes = test_store["objects"][artifact.path]
    assert artifact.size == len(stored_bytes)
    assert artifact.sha256 == hashlib.sha256(stored_bytes).hexdigest()

    assert len(test_store["render_delay_payloads"]) == 1
    assert test_store["render_delay_payloads"][0]["job"]["job_id"] == str(job.job_id)
    assert test_store["render_delay_payloads"][0]["job"]["status"] == JobStatus.CODED.value


def test_generate_code_failure_sets_failed_codegen(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_paths,
    mock_worker_storage,
    mock_worker_budget,
    sample_video_plan,
    test_store,
):
    from app.workers import worker as worker_module

    def fake_render_codegen_prompt(plan):
        return "fake-system-prompt", "fake-user-query"

    def failing_codegen_call(system_prompt, user_query):
        raise RuntimeError("codegen failed")

    monkeypatch.setattr(worker_module.LLMService, "render_codegen_prompt", staticmethod(fake_render_codegen_prompt))
    monkeypatch.setattr(worker_module.LLMService, "codegen_call", staticmethod(failing_codegen_call))

    job = Job(status=JobStatus.APPROVED)
    test_store["jobs"][job.job_id] = job
    payload = JobPlanRequest(job=job, plan=sample_video_plan).model_dump(mode="json")

    with pytest.raises(RuntimeError, match="codegen failed"):
        worker_module.generate_code(payload)

    assert test_store["jobs"][job.job_id].status == JobStatus.FAILED_CODEGEN
    assert test_store["status_updates"][-1] == (job.job_id, JobStatus.FAILED_CODEGEN)


def test_generate_code_verification_failure_transitions_to_failed_codegen(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_paths,
    mock_worker_storage,
    mock_worker_llm,
    mock_worker_budget,
    sample_video_plan,
    test_store,
):
    """When verify_code always fails, max retries are exhausted → FAILED_CODEGEN."""
    from app.workers import worker as worker_module
    from celery.exceptions import MaxRetriesExceededError

    monkeypatch.setattr(worker_module, "verify_code", lambda code: ["Forbidden imports: os"])

    # Simulate Celery exhausting retries: self.retry raises MaxRetriesExceededError
    def fake_retry(*args, exc=None, **kwargs):
        raise MaxRetriesExceededError()

    monkeypatch.setattr(worker_module.generate_code, "retry", fake_retry)

    job = Job(status=JobStatus.APPROVED)
    test_store["jobs"][job.job_id] = job
    payload = JobPlanRequest(job=job, plan=sample_video_plan).model_dump(mode="json")

    with pytest.raises(MaxRetriesExceededError):
        worker_module.generate_code(payload)

    assert test_store["jobs"][job.job_id].status == JobStatus.FAILED_CODEGEN
    assert test_store["status_updates"][-1] == (job.job_id, JobStatus.FAILED_CODEGEN)


def test_generate_code_verification_failure_does_not_store_artifact(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_paths,
    mock_worker_storage,
    mock_worker_llm,
    mock_worker_budget,
    sample_video_plan,
    test_store,
):
    """Unverified code must never be persisted as an artifact."""
    from app.workers import worker as worker_module
    from celery.exceptions import MaxRetriesExceededError

    monkeypatch.setattr(worker_module, "verify_code", lambda code: ["mypy errors: bad type"])

    def fake_retry(*args, exc=None, **kwargs):
        raise MaxRetriesExceededError()

    monkeypatch.setattr(worker_module.generate_code, "retry", fake_retry)

    job = Job(status=JobStatus.APPROVED)
    test_store["jobs"][job.job_id] = job
    payload = JobPlanRequest(job=job, plan=sample_video_plan).model_dump(mode="json")

    with pytest.raises(MaxRetriesExceededError):
        worker_module.generate_code(payload)

    job_artifacts = [a for a in test_store["artifacts"].values() if a.job_id == job.job_id]
    assert len(job_artifacts) == 0, "No artifact should be stored when verification fails"


# ---------------------------------------------------------------------------
# generate_render tests
# ---------------------------------------------------------------------------

def _make_render_payload(job, sample_video_plan, test_store):
    test_store["plans"][job.job_id] = Plan(
        job_id=job.job_id,
        plan=sample_video_plan.model_dump_json(),
        approved=True,
    )
    code_bytes = (
        b"from manim import *\n\n"
        b"class Scene1(Scene):\n"
        b"    def construct(self):\n"
        b"        self.wait()\n"
    )
    object_name = f"{job.job_id}/lesson.py"
    test_store["objects"][object_name] = code_bytes
    code_artifact = Artifact(
        artifact_id=uuid4(),
        job_id=job.job_id,
        artifact_type=ArtifactType.PYTHON_FILE,
        path=object_name,
        size=len(code_bytes),
        sha256=hashlib.sha256(code_bytes).hexdigest(),
    )
    test_store["artifacts"][code_artifact.artifact_id] = code_artifact
    return JobRequest(job=job).model_dump(mode="json")


def test_generate_render_success_invokes_renderer_and_persists_mp4_artifacts(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_paths,
    mock_worker_storage,
    sample_video_plan,
    test_store,
):
    from app.workers import worker as worker_module

    job = Job(status=JobStatus.CODED)
    test_store["jobs"][job.job_id] = job
    payload = _make_render_payload(job, sample_video_plan, test_store)

    def fake_run(command, *, capture_output, text, timeout):
        test_store["subprocess_commands"].append(command)
        media_dir = Path(command[-2])
        code_path = Path(command[-1])
        videos_dir = (
            media_dir
            / worker_module.PathNames.VIDEOS_FOLDER
            / code_path.stem
            / worker_module.PathNames.RESOLUTION_FOLDER
        )
        videos_dir.mkdir(parents=True, exist_ok=True)
        for index, _ in enumerate(sample_video_plan.scenes, start=1):
            (videos_dir / f"scene_{index}.mp4").write_bytes(b"mp4-bytes")
        return subprocess.CompletedProcess(command, 0, "render stdout", "render stderr")

    monkeypatch.setattr(worker_module.subprocess, "run", fake_run)

    worker_module.generate_render(payload)

    assert test_store["jobs"][job.job_id].status == JobStatus.RENDERED
    assert test_store["status_updates"][-2:] == [
        (job.job_id, JobStatus.RENDERING),
        (job.job_id, JobStatus.RENDERED),
    ]

    mp4_artifacts = [
        a for a in test_store["artifacts"].values()
        if a.job_id == job.job_id and a.artifact_type == ArtifactType.MP4
    ]
    assert len(mp4_artifacts) == len(sample_video_plan.scenes)

    log_artifacts = [
        a for a in test_store["artifacts"].values()
        if a.job_id == job.job_id and a.artifact_type == ArtifactType.LOG
    ]
    assert len(log_artifacts) == 2
    log_names = {Path(a.path).name for a in log_artifacts}
    assert log_names == {"render_stdout.log", "render_stderr.log"}

    assert len(test_store["subprocess_commands"]) == 1
    command = test_store["subprocess_commands"][0]
    assert "--network" in command and "none" in command
    assert "--cpus" in command
    assert "--memory" in command
    assert "--pids-limit" in command
    assert "--security-opt" in command and "no-new-privileges" in command


def test_generate_render_failure_sets_failed_render_and_stores_logs(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_paths,
    mock_worker_storage,
    sample_video_plan,
    test_store,
):
    from app.workers import worker as worker_module

    job = Job(status=JobStatus.CODED)
    test_store["jobs"][job.job_id] = job
    payload = _make_render_payload(job, sample_video_plan, test_store)

    def failing_run(command, *, capture_output, text, timeout):
        return subprocess.CompletedProcess(command, 1, "error stdout", "error stderr")

    monkeypatch.setattr(worker_module.subprocess, "run", failing_run)

    with pytest.raises(RuntimeError, match="Docker render exited with code 1"):
        worker_module.generate_render(payload)

    assert test_store["jobs"][job.job_id].status == JobStatus.FAILED_RENDER
    assert test_store["status_updates"][-1] == (job.job_id, JobStatus.FAILED_RENDER)

    log_artifacts = [
        a for a in test_store["artifacts"].values()
        if a.job_id == job.job_id and a.artifact_type == ArtifactType.LOG
    ]
    assert len(log_artifacts) == 2
    log_names = {Path(a.path).name for a in log_artifacts}
    assert log_names == {"render_stdout.log", "render_stderr.log"}


def test_generate_render_timeout_sets_failed_render(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_paths,
    mock_worker_storage,
    sample_video_plan,
    test_store,
):
    from app.workers import worker as worker_module

    job = Job(status=JobStatus.CODED)
    test_store["jobs"][job.job_id] = job
    payload = _make_render_payload(job, sample_video_plan, test_store)

    def timeout_run(command, *, capture_output, text, timeout):
        raise subprocess.TimeoutExpired(cmd=command, timeout=timeout, output="", stderr="")

    monkeypatch.setattr(worker_module.subprocess, "run", timeout_run)

    with pytest.raises(subprocess.TimeoutExpired):
        worker_module.generate_render(payload)

    assert test_store["jobs"][job.job_id].status == JobStatus.FAILED_RENDER
    assert test_store["status_updates"][-1] == (job.job_id, JobStatus.FAILED_RENDER)


def test_generate_render_no_plan_sets_failed_render(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_paths,
    mock_worker_storage,
    sample_video_plan,
    test_store,
):
    from app.workers import worker as worker_module

    job = Job(status=JobStatus.CODED)
    test_store["jobs"][job.job_id] = job
    # Do NOT add a plan to test_store
    payload = JobRequest(job=job).model_dump(mode="json")

    with pytest.raises(RuntimeError, match="No plan found"):
        worker_module.generate_render(payload)

    assert test_store["jobs"][job.job_id].status == JobStatus.FAILED_RENDER


def test_generate_render_no_python_artifact_sets_failed_render(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_paths,
    mock_worker_storage,
    sample_video_plan,
    test_store,
):
    from app.workers import worker as worker_module

    job = Job(status=JobStatus.CODED)
    test_store["jobs"][job.job_id] = job
    test_store["plans"][job.job_id] = Plan(
        job_id=job.job_id,
        plan=sample_video_plan.model_dump_json(),
        approved=True,
    )
    # Do NOT add any artifacts
    payload = JobRequest(job=job).model_dump(mode="json")

    with pytest.raises(RuntimeError, match="No python code artifact"):
        worker_module.generate_render(payload)

    assert test_store["jobs"][job.job_id].status == JobStatus.FAILED_RENDER


def test_generate_render_log_storage_failure_does_not_block_render_success(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_paths,
    mock_worker_storage,
    sample_video_plan,
    test_store,
):
    """store_render_logs is best-effort; a MinIO write error must not propagate."""
    from app.workers import worker as worker_module
    from app.workers import worker_helpers

    job = Job(status=JobStatus.CODED)
    test_store["jobs"][job.job_id] = job
    payload = _make_render_payload(job, sample_video_plan, test_store)

    def fake_run(command, *, capture_output, text, timeout):
        media_dir = Path(command[-2])
        code_path = Path(command[-1])
        videos_dir = (
            media_dir
            / worker_module.PathNames.VIDEOS_FOLDER
            / code_path.stem
            / worker_module.PathNames.RESOLUTION_FOLDER
        )
        videos_dir.mkdir(parents=True, exist_ok=True)
        for index, _ in enumerate(sample_video_plan.scenes, start=1):
            (videos_dir / f"scene_{index}.mp4").write_bytes(b"mp4-bytes")
        return subprocess.CompletedProcess(command, 0, "stdout", "stderr")

    monkeypatch.setattr(worker_module.subprocess, "run", fake_run)

    # Make save_artifact raise for .log files — store_render_logs must swallow it
    original_save = worker_helpers.FilesStorageService.save_artifact

    def failing_save_for_logs(self, job_id, file_path):
        if str(file_path).endswith(".log"):
            raise OSError("disk full")
        return original_save(self, job_id, file_path)

    monkeypatch.setattr(worker_helpers.FilesStorageService, "save_artifact", failing_save_for_logs)

    # Should not raise despite log storage failure
    worker_module.generate_render(payload)

    assert test_store["jobs"][job.job_id].status == JobStatus.RENDERED
