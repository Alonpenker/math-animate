import hashlib
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

from app.domain.job_state import JobStatus
from app.exceptions.llm_usage_exception import LLMUsageException
from app.exceptions.quota_exceeded_error import QuotaExceededError
from app.schemas.artifact import Artifact, ArtifactType
from app.schemas.jobs import Job, JobCodeRequest, JobFixRequest, JobPlanRequest, JobRequest, JobUserRequest
from app.schemas.plan import Plan

def _patch_mypy_pass(monkeypatch):
    from app.workers import worker_helpers

    monkeypatch.setattr(
        worker_helpers.subprocess,
        "run",
        lambda cmd, *, capture_output, text, timeout: subprocess.CompletedProcess(cmd, 0, "", ""),
    )

def _setup_dry_run_env(monkeypatch, tmp_path):
    from app.workers import worker_helpers

    render_root = tmp_path / "render_root"
    render_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(worker_helpers.PathNames, "TMP_RENDER_FOLDER", str(render_root))

    input_dir = render_root / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    code_path = input_dir / "code.py"
    code_path.write_text("from manim import *\n", encoding="utf-8")

    media_dir = input_dir / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    return code_path, media_dir

def test_verify_code_passes_valid_manim_code(monkeypatch):
    # Given
    from app.workers.worker_helpers import verify_code
    _patch_mypy_pass(monkeypatch)
    code = (
        "from manim import *\n\n"
        "class Scene1(Scene):\n"
        "    def construct(self):\n"
        "        self.wait()\n"
    )

    # When
    failure = verify_code(code, Path("/tmp/fake.py"))

    # Then
    assert failure is None

def test_verify_code_fails_when_mypy_reports_errors(monkeypatch):
    # Given
    from app.workers import worker_helpers
    from app.workers.worker_helpers import verify_code

    monkeypatch.setattr(
        worker_helpers.subprocess,
        "run",
        lambda cmd, *, capture_output, text, timeout: subprocess.CompletedProcess(
            cmd, 1, "error: some type error\n", ""
        ),
    )
    code = "from manim import *\n"

    # When
    failure = verify_code(code, Path("/tmp/fake.py"))

    # Then
    assert failure is not None
    assert "mypy errors" in failure

def test_verify_code_fails_on_forbidden_import_os(monkeypatch):
    # Given
    from app.workers.worker_helpers import verify_code
    _patch_mypy_pass(monkeypatch)
    code = "import os\nfrom manim import *\n"

    # When
    failure = verify_code(code, Path("/tmp/fake.py"))

    # Then
    assert failure is not None
    assert "os" in failure

def test_verify_code_fails_on_from_import_of_forbidden_module(monkeypatch):
    # Given
    from app.workers.worker_helpers import verify_code
    _patch_mypy_pass(monkeypatch)
    code = "from subprocess import run\nfrom manim import *\n"

    # When
    failure = verify_code(code, Path("/tmp/fake.py"))

    # Then
    assert failure is not None
    assert "subprocess" in failure

def test_verify_code_fails_on_dangerous_builtin_exec(monkeypatch):
    # Given
    from app.workers.worker_helpers import verify_code
    _patch_mypy_pass(monkeypatch)
    code = "from manim import *\nexec('print(1)')\n"

    # When
    failure = verify_code(code, Path("/tmp/fake.py"))

    # Then
    assert failure is not None
    assert "exec" in failure

def test_verify_code_fails_on_dangerous_builtin_eval(monkeypatch):
    # Given
    from app.workers.worker_helpers import verify_code
    _patch_mypy_pass(monkeypatch)
    code = "from manim import *\nx = eval('1+1')\n"

    # When
    failure = verify_code(code, Path("/tmp/fake.py"))

    # Then
    assert failure is not None
    assert "eval" in failure

def test_verify_code_fails_on_syntax_error(monkeypatch):
    # Given
    from app.workers.worker_helpers import verify_code
    _patch_mypy_pass(monkeypatch)
    code = "from manim import *\ndef broken(:\n"

    # When
    failure = verify_code(code, Path("/tmp/fake.py"))

    # Then
    assert failure is not None
    assert "syntax error" in failure.lower()

def test_verify_code_allows_all_permitted_imports(monkeypatch):
    # Given
    from app.workers.worker_helpers import verify_code
    _patch_mypy_pass(monkeypatch)
    code = (
        "import math\nimport random\nimport typing\n"
        "import numpy as np\nfrom manim import *\nfrom colour import Color\n"
    )

    # When
    failure = verify_code(code, Path("/tmp/fake.py"))

    # Then
    assert failure is None

def test_verify_code_reports_all_forbidden_modules_in_single_message(monkeypatch):
    # Given
    from app.workers.worker_helpers import verify_code
    _patch_mypy_pass(monkeypatch)
    code = "import os\nimport sys\nfrom manim import *\n"

    # When
    failure = verify_code(code, Path("/tmp/fake.py"))

    # Then — both forbidden modules appear in one combined failure message
    assert failure is not None
    assert "os" in failure
    assert "sys" in failure

def test_extract_traceback_returns_from_marker_to_end():
    # Given
    from app.workers.worker_helpers import extract_traceback
    stderr = (
        "INFO manim starting...\n"
        "Rendering scene...\n"
        "Traceback (most recent call last):\n"
        "  File code.py, line 5, in construct\n"
        "IndexError: list index out of range\n"
    )

    # When
    result = extract_traceback(stderr)

    # Then
    assert result.startswith("Traceback (most recent call last):")
    assert "IndexError" in result
    assert "INFO manim starting" not in result

def test_extract_traceback_returns_full_string_when_no_traceback_marker_present():
    # Given
    from app.workers.worker_helpers import extract_traceback
    stderr = "Error: some plain error without traceback"

    # When
    result = extract_traceback(stderr)

    # Then
    assert result == stderr

def test_extract_traceback_handles_empty_string():
    # Given
    from app.workers.worker_helpers import extract_traceback

    # When
    result = extract_traceback("")

    # Then
    assert result == ""

def test_dry_run_docker_passes_when_subprocess_exits_zero(monkeypatch, tmp_path):
    # Given
    from app.workers import worker_helpers
    from app.workers.worker_helpers import dry_run_docker
    code_path, media_dir = _setup_dry_run_env(monkeypatch, tmp_path)
    monkeypatch.setattr(
        worker_helpers.subprocess, "run",
        lambda cmd, *, capture_output, text, timeout, input=None: subprocess.CompletedProcess(cmd, 0, "", ""),
    )

    # When
    passed, error, is_fixable = dry_run_docker(code_path, media_dir)

    # Then
    assert passed is True
    assert error == ""
    assert is_fixable is True

def test_dry_run_docker_command_includes_manim_dry_run_flag(monkeypatch, tmp_path):
    # Given
    from app.workers import worker_helpers
    from app.workers.worker_helpers import dry_run_docker
    code_path, media_dir = _setup_dry_run_env(monkeypatch, tmp_path)
    captured_commands = []

    def fake_run(cmd, *, capture_output, text, timeout, input=None):
        captured_commands.append(list(cmd))
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(worker_helpers.subprocess, "run", fake_run)

    # When
    dry_run_docker(code_path, media_dir)

    # Then
    assert len(captured_commands) == 1
    cmd = captured_commands[0]
    assert "manim" in cmd
    assert "--dry_run" in cmd

def test_dry_run_docker_extracts_traceback_from_stderr_on_nonzero_exit(monkeypatch, tmp_path):
    # Given
    from app.workers import worker_helpers
    from app.workers.worker_helpers import dry_run_docker
    code_path, media_dir = _setup_dry_run_env(monkeypatch, tmp_path)
    stderr_with_noise = (
        "INFO manim starting\n"
        "Traceback (most recent call last):\n"
        "  File code.py, line 5\n"
        "IndexError: list index out of range\n"
    )
    monkeypatch.setattr(
        worker_helpers.subprocess, "run",
        lambda cmd, *, capture_output, text, timeout, input=None: subprocess.CompletedProcess(
            cmd, 1, "some stdout", stderr_with_noise
        ),
    )

    # When
    passed, error, is_fixable = dry_run_docker(code_path, media_dir)

    # Then
    assert passed is False
    assert error.startswith("Traceback (most recent call last):")
    assert "IndexError" in error
    assert "INFO manim starting" not in error
    assert "some stdout" not in error
    assert is_fixable is True

def test_dry_run_docker_returns_full_stderr_when_no_traceback_marker(monkeypatch, tmp_path):
    # Given
    from app.workers import worker_helpers
    from app.workers.worker_helpers import dry_run_docker
    code_path, media_dir = _setup_dry_run_env(monkeypatch, tmp_path)
    monkeypatch.setattr(
        worker_helpers.subprocess, "run",
        lambda cmd, *, capture_output, text, timeout, input=None: subprocess.CompletedProcess(
            cmd, 1, "", "plain error message"
        ),
    )

    # When
    passed, error, is_fixable = dry_run_docker(code_path, media_dir)

    # Then
    assert passed is False
    assert error == "plain error message"
    assert is_fixable is True

def test_dry_run_docker_handles_timeout_and_reports_stderr(monkeypatch, tmp_path):
    # Given
    from app.workers import worker_helpers
    from app.workers.worker_helpers import dry_run_docker
    code_path, media_dir = _setup_dry_run_env(monkeypatch, tmp_path)

    def timeout_run(cmd, *, capture_output, text, timeout, input=None):
        raise subprocess.TimeoutExpired(
            cmd=cmd, timeout=timeout, output=b"stdout-timeout", stderr=b"stderr-timeout"
        )

    monkeypatch.setattr(worker_helpers.subprocess, "run", timeout_run)

    # When
    passed, error, is_fixable = dry_run_docker(code_path, media_dir)

    # Then
    assert passed is False
    assert "Dry-run timed out after 90s." in error
    assert is_fixable is False


def test_generate_plan_transitions_to_planned_and_persists_plan(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    sample_user_request,
    sample_video_plan,
    test_store,
):
    # Given
    from app.services.openrouter_service import OpenRouterTokenUsage
    from app.workers import worker as worker_module

    monkeypatch.setattr(
        worker_module.OpenRouterService,
        "invoke_structured",
        staticmethod(lambda **kwargs: (sample_video_plan, OpenRouterTokenUsage(total_tokens=123))),
    )

    job = Job(status=JobStatus.CREATED)
    test_store["jobs"][job.job_id] = job
    payload = JobUserRequest(job=job, user_request=sample_user_request).model_dump(mode="json")

    # When
    worker_module.generate_plan(payload)

    # Then
    assert test_store["jobs"][job.job_id].status == JobStatus.PLANNED
    assert job.job_id in test_store["plans"]
    assert test_store["status_updates"][-2:] == [
        (job.job_id, JobStatus.PLANNING),
        (job.job_id, JobStatus.PLANNED),
    ]

def test_generate_plan_sets_failed_quota_exceeded_and_reraises(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    sample_user_request,
    test_store,
):
    # Given
    from app.workers import worker as worker_module

    monkeypatch.setattr(
        worker_module.OpenRouterService,
        "invoke_structured",
        staticmethod(lambda **kwargs: (_ for _ in ()).throw(
            QuotaExceededError(limit=50, consumed=50, reserved=0, requested=1)
        )),
    )

    job = Job(status=JobStatus.CREATED)
    test_store["jobs"][job.job_id] = job
    payload = JobUserRequest(job=job, user_request=sample_user_request).model_dump(mode="json")

    # When / Then
    with pytest.raises(QuotaExceededError):
        worker_module.generate_plan(payload)

    assert test_store["jobs"][job.job_id].status == JobStatus.FAILED_QUOTA_EXCEEDED
    assert test_store["status_updates"][-1] == (job.job_id, JobStatus.FAILED_QUOTA_EXCEEDED)

def test_worker_runner_routes_created_jobs_to_planning(monkeypatch):
    # Given
    from app.workers import runner as runner_module

    enqueued = []
    monkeypatch.setattr(
        runner_module.generate_plan,
        "delay",
        lambda payload: enqueued.append(payload),
    )
    job_request = JobRequest(job=Job(status=JobStatus.CREATED))

    # When
    runner_module.WorkerRunner.handle_planning(job_request)

    # Then
    assert len(enqueued) == 1
    assert enqueued[0]["job"]["status"] == JobStatus.CREATED.value

def test_worker_runner_routes_approved_jobs_to_codegen(monkeypatch):
    # Given
    from app.workers import runner as runner_module

    enqueued = []
    monkeypatch.setattr(
        runner_module.generate_code,
        "delay",
        lambda payload: enqueued.append(payload),
    )
    job_request = JobRequest(job=Job(status=JobStatus.APPROVED))

    # When
    runner_module.WorkerRunner.handle_codegen(job_request)

    # Then
    assert len(enqueued) == 1
    assert enqueued[0]["job"]["status"] == JobStatus.APPROVED.value

def _make_render_payload(job, sample_video_plan, test_store):
    test_store["plans"][job.job_id] = Plan(
        job_id=job.job_id, plan=sample_video_plan, approved=True
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

def test_generate_render_invokes_docker_and_persists_mp4_and_log_artifacts(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_paths,
    mock_worker_storage,
    sample_video_plan,
    test_store,
):
    # Given
    from app.workers import worker as worker_module

    job = Job(status=JobStatus.VERIFIED)
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

    # When
    worker_module.generate_render(payload)

    # Then
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
    assert {Path(a.path).name for a in log_artifacts} == {"render_stdout.log", "render_stderr.log"}

    cmd = test_store["subprocess_commands"][0]
    assert "--network" in cmd and "none" in cmd
    assert "--cpus" in cmd
    assert "--memory" in cmd
    assert "--pids-limit" in cmd
    assert "--security-opt" in cmd and "no-new-privileges" in cmd

def test_generate_render_sets_failed_render_and_stores_logs_on_docker_nonzero_exit(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_paths,
    mock_worker_storage,
    sample_video_plan,
    test_store,
):
    # Given
    from app.workers import worker as worker_module

    job = Job(status=JobStatus.VERIFIED)
    test_store["jobs"][job.job_id] = job
    payload = _make_render_payload(job, sample_video_plan, test_store)

    monkeypatch.setattr(
        worker_module.subprocess, "run",
        lambda cmd, *, capture_output, text, timeout: subprocess.CompletedProcess(
            cmd, 1, "error stdout", "error stderr"
        ),
    )

    # When / Then
    with pytest.raises(RuntimeError, match="Docker render exited with code 1"):
        worker_module.generate_render(payload)

    assert test_store["jobs"][job.job_id].status == JobStatus.FAILED_RENDER
    log_artifacts = [
        a for a in test_store["artifacts"].values()
        if a.job_id == job.job_id and a.artifact_type == ArtifactType.LOG
    ]
    assert len(log_artifacts) == 2

def test_generate_render_sets_failed_render_on_subprocess_timeout(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_paths,
    mock_worker_storage,
    sample_video_plan,
    test_store,
):
    # Given
    from app.workers import worker as worker_module

    job = Job(status=JobStatus.VERIFIED)
    test_store["jobs"][job.job_id] = job
    payload = _make_render_payload(job, sample_video_plan, test_store)

    monkeypatch.setattr(
        worker_module.subprocess, "run",
        lambda cmd, *, capture_output, text, timeout: (_ for _ in ()).throw(
            subprocess.TimeoutExpired(cmd=cmd, timeout=timeout, output="", stderr="")
        ),
    )

    # When / Then
    with pytest.raises(subprocess.TimeoutExpired):
        worker_module.generate_render(payload)

    assert test_store["jobs"][job.job_id].status == JobStatus.FAILED_RENDER

def test_generate_render_sets_failed_render_when_plan_is_missing(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_paths,
    mock_worker_storage,
    test_store,
):
    # Given
    from app.workers import worker as worker_module

    job = Job(status=JobStatus.VERIFIED)
    test_store["jobs"][job.job_id] = job
    payload = JobRequest(job=job).model_dump(mode="json")

    # When / Then
    with pytest.raises(RuntimeError, match="No plan found"):
        worker_module.generate_render(payload)

    assert test_store["jobs"][job.job_id].status == JobStatus.FAILED_RENDER

def test_generate_render_sets_failed_render_when_python_artifact_is_missing(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_paths,
    mock_worker_storage,
    sample_video_plan,
    test_store,
):
    # Given
    from app.workers import worker as worker_module

    job = Job(status=JobStatus.VERIFIED)
    test_store["jobs"][job.job_id] = job
    test_store["plans"][job.job_id] = Plan(
        job_id=job.job_id, plan=sample_video_plan, approved=True
    )
    payload = JobRequest(job=job).model_dump(mode="json")

    # When / Then
    with pytest.raises(RuntimeError, match="No python code artifact"):
        worker_module.generate_render(payload)

    assert test_store["jobs"][job.job_id].status == JobStatus.FAILED_RENDER

def test_generate_render_succeeds_even_when_log_storage_raises(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_paths,
    mock_worker_storage,
    sample_video_plan,
    test_store,
):
    # Given — store_render_logs is best-effort; MinIO write failures must not block RENDERED status
    from app.workers import worker as worker_module
    from app.workers import worker_helpers

    job = Job(status=JobStatus.VERIFIED)
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

    original_save = worker_helpers.FilesStorageService.save_artifact

    def failing_save_for_logs(self, job_id, file_path):
        if str(file_path).endswith(".log"):
            raise OSError("disk full")
        return original_save(self, job_id, file_path)

    monkeypatch.setattr(worker_helpers.FilesStorageService, "save_artifact", failing_save_for_logs)

    # When
    worker_module.generate_render(payload)

    # Then
    assert test_store["jobs"][job.job_id].status == JobStatus.RENDERED
