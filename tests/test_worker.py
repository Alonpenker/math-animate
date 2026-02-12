import hashlib
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

from app.domain.job_state import JobStatus
from app.schemas.artifact import Artifact, ArtifactType
from app.schemas.jobs import Job, JobPlanRequest, JobRequest, JobUserRequest
from app.schemas.plan import Plan


def test_generate_plan_success_transitions_and_saves_plan(
    mock_repositories,
    mock_worker_cursor,
    mock_worker_llm,
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
    sample_user_request,
    test_store,
):
    from app.workers import worker as worker_module

    def failing_plan_call(user_request):
        raise RuntimeError("planning failed")

    monkeypatch.setattr(worker_module.LLMService, "plan_call", staticmethod(failing_plan_call))

    job = Job(status=JobStatus.CREATED)
    test_store["jobs"][job.job_id] = job
    payload = JobUserRequest(job=job, user_request=sample_user_request).model_dump(mode="json")

    with pytest.raises(RuntimeError, match="planning failed"):
        worker_module.generate_plan(payload)

    assert test_store["jobs"][job.job_id].status == JobStatus.FAILED_PLANNING
    assert test_store["status_updates"][-1] == (job.job_id, JobStatus.FAILED_PLANNING)


def test_generate_code_success_persists_python_artifact_and_enqueues_render(
    mock_repositories,
    mock_worker_cursor,
    mock_worker_paths,
    mock_worker_storage,
    mock_worker_llm,
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

    job_artifacts = [
        artifact
        for artifact in test_store["artifacts"].values()
        if artifact.job_id == job.job_id
    ]
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
    sample_video_plan,
    test_store,
):
    from app.workers import worker as worker_module

    def failing_codegen_call(plan):
        raise RuntimeError("codegen failed")

    monkeypatch.setattr(worker_module.LLMService, "codegen_call", staticmethod(failing_codegen_call))

    job = Job(status=JobStatus.APPROVED)
    test_store["jobs"][job.job_id] = job
    payload = JobPlanRequest(job=job, plan=sample_video_plan).model_dump(mode="json")

    with pytest.raises(RuntimeError, match="codegen failed"):
        worker_module.generate_code(payload)

    assert test_store["jobs"][job.job_id].status == JobStatus.FAILED_CODEGEN
    assert test_store["status_updates"][-1] == (job.job_id, JobStatus.FAILED_CODEGEN)


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

    def fake_run(command, check, stdout, stderr, text):
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
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(worker_module.subprocess, "run", fake_run)

    payload = JobRequest(job=job).model_dump(mode="json")
    worker_module.generate_render(payload)

    assert test_store["jobs"][job.job_id].status == JobStatus.RENDERED
    assert test_store["status_updates"][-2:] == [
        (job.job_id, JobStatus.RENDERING),
        (job.job_id, JobStatus.RENDERED),
    ]

    mp4_artifacts = [
        artifact
        for artifact in test_store["artifacts"].values()
        if artifact.job_id == job.job_id and artifact.artifact_type == ArtifactType.MP4
    ]
    assert len(mp4_artifacts) == len(sample_video_plan.scenes)

    assert len(test_store["subprocess_commands"]) == 1
    command = test_store["subprocess_commands"][0]
    assert "--network" in command and "none" in command
    assert "--cpus" in command
    assert "--memory" in command
    assert "--pids-limit" in command
    assert "--security-opt" in command and "no-new-privileges" in command


def test_generate_render_failure_sets_failed_render(
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

    code_bytes = b"from manim import *\n"
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

    def failing_run(command, check, stdout, stderr, text):
        raise subprocess.CalledProcessError(
            returncode=1,
            cmd=command,
            output="stdout error",
            stderr="stderr error",
        )

    monkeypatch.setattr(worker_module.subprocess, "run", failing_run)

    payload = JobRequest(job=job).model_dump(mode="json")
    with pytest.raises(subprocess.CalledProcessError):
        worker_module.generate_render(payload)

    assert test_store["jobs"][job.job_id].status == JobStatus.FAILED_RENDER
    assert test_store["status_updates"][-1] == (job.job_id, JobStatus.FAILED_RENDER)
