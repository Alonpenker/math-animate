"""
Worker pipeline tests.

Covers three groups:
  1. Utility functions (verify_code, extract_traceback, dry_run_docker) —
     pure unit tests, no DB/storage/Celery mocks needed.
  2. Celery task functions (generate_plan, generate_code, verify_code_task,
     fix_code_task, generate_render) — use the mock_worker_* fixture family.
"""
import hashlib
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest

from app.domain.job_state import JobStatus
from app.schemas.artifact import Artifact, ArtifactType
from app.schemas.jobs import Job, JobCodeRequest, JobFixRequest, JobPlanRequest, JobRequest, JobUserRequest
from app.schemas.plan import Plan


# ─────────────────────────────────────────────────────────────────────────────
# Helpers shared across verify_code / dry_run_docker tests
# ─────────────────────────────────────────────────────────────────────────────

def _patch_mypy_pass(monkeypatch):
    """Make subprocess.run report mypy success (returncode 0)."""
    from app.workers import worker_helpers

    monkeypatch.setattr(
        worker_helpers.subprocess,
        "run",
        lambda cmd, *, capture_output, text, timeout: subprocess.CompletedProcess(cmd, 0, "", ""),
    )


def _setup_dry_run_env(monkeypatch, tmp_path):
    """
    Create minimal filesystem state and return (code_path, media_dir) for
    dry_run_docker tests.
    """
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


# ─────────────────────────────────────────────────────────────────────────────
# verify_code — static analysis of generated Manim code
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# extract_traceback — isolates Python traceback from noisy stderr
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# dry_run_docker — runs Manim --dry_run in a subprocess
# ─────────────────────────────────────────────────────────────────────────────

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
    assert "Dry-run timed out after 60s." in error
    assert is_fixable is False


# ─────────────────────────────────────────────────────────────────────────────
# generate_plan
# ─────────────────────────────────────────────────────────────────────────────

def test_generate_plan_transitions_to_planned_and_persists_plan(
    mock_repositories,
    mock_worker_cursor,
    mock_worker_llm,
    mock_worker_budget,
    sample_user_request,
    test_store,
):
    # Given
    from app.workers import worker as worker_module

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


def test_generate_plan_sets_failed_planning_and_reraises_on_llm_error(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_budget,
    sample_user_request,
    test_store,
):
    # Given
    from app.workers import worker as worker_module

    monkeypatch.setattr(
        worker_module.LLMService, "render_plan_prompt",
        staticmethod(lambda user_request: ("fake-system-prompt", "fake-user-query")),
    )
    monkeypatch.setattr(
        worker_module.LLMService, "plan_call",
        staticmethod(lambda system_prompt, user_query: (_ for _ in ()).throw(RuntimeError("planning failed"))),
    )

    job = Job(status=JobStatus.CREATED)
    test_store["jobs"][job.job_id] = job
    payload = JobUserRequest(job=job, user_request=sample_user_request).model_dump(mode="json")

    # When / Then
    with pytest.raises(RuntimeError, match="planning failed"):
        worker_module.generate_plan(payload)

    assert test_store["jobs"][job.job_id].status == JobStatus.FAILED_PLANNING
    assert test_store["status_updates"][-1] == (job.job_id, JobStatus.FAILED_PLANNING)


# ─────────────────────────────────────────────────────────────────────────────
# generate_code
# ─────────────────────────────────────────────────────────────────────────────

def test_generate_code_transitions_to_coded_and_enqueues_verify(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_llm,
    mock_worker_budget,
    sample_video_plan,
    test_store,
):
    # Given
    from app.workers import worker as worker_module

    enqueued = []
    monkeypatch.setattr(
        worker_module.verify_code_task, "delay", lambda payload: enqueued.append(payload)
    )

    job = Job(status=JobStatus.APPROVED)
    test_store["jobs"][job.job_id] = job
    payload = JobPlanRequest(job=job, plan=sample_video_plan).model_dump(mode="json")

    # When
    worker_module.generate_code(payload)

    # Then
    assert test_store["jobs"][job.job_id].status == JobStatus.CODED
    assert test_store["status_updates"][-2:] == [
        (job.job_id, JobStatus.CODEGEN),
        (job.job_id, JobStatus.CODED),
    ]
    assert len(enqueued) == 1
    assert enqueued[0]["job"]["job_id"] == str(job.job_id)
    assert enqueued[0]["is_retry"] is False


def test_generate_code_sets_failed_codegen_and_reraises_on_llm_error(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_budget,
    sample_video_plan,
    test_store,
):
    # Given
    from app.workers import worker as worker_module

    monkeypatch.setattr(
        worker_module.LLMService, "render_codegen_prompt",
        staticmethod(lambda plan: ("fake-system-prompt", "fake-user-query")),
    )
    monkeypatch.setattr(
        worker_module.LLMService, "codegen_call",
        staticmethod(lambda sp, uq: (_ for _ in ()).throw(RuntimeError("codegen failed"))),
    )

    job = Job(status=JobStatus.APPROVED)
    test_store["jobs"][job.job_id] = job
    payload = JobPlanRequest(job=job, plan=sample_video_plan).model_dump(mode="json")

    # When / Then
    with pytest.raises(RuntimeError, match="codegen failed"):
        worker_module.generate_code(payload)

    assert test_store["jobs"][job.job_id].status == JobStatus.FAILED_CODEGEN


# ─────────────────────────────────────────────────────────────────────────────
# verify_code_task
# ─────────────────────────────────────────────────────────────────────────────

def test_verify_code_task_saves_artifact_and_enqueues_render_on_success(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_paths,
    mock_worker_storage,
    capture_render_delay,
    sample_video_plan,
    test_store,
):
    # Given
    from app.workers import worker as worker_module
    from app.workers import worker_helpers

    monkeypatch.setattr(worker_helpers, "verify_code", lambda code, code_path: None)
    monkeypatch.setattr(
        worker_module, "dry_run_docker", lambda code_path, media_dir: (True, "", True)
    )

    code = (
        "from manim import *\n\n"
        "class Scene1(Scene):\n"
        "    def construct(self):\n"
        "        self.wait()\n"
    )
    job = Job(status=JobStatus.CODED)
    test_store["jobs"][job.job_id] = job
    payload = JobCodeRequest(
        job=Job(job_id=job.job_id, status=JobStatus.CODED),
        code=code,
        is_retry=False,
    ).model_dump(mode="json")

    # When
    worker_module.verify_code_task(payload)

    # Then
    assert test_store["jobs"][job.job_id].status == JobStatus.VERIFIED
    assert test_store["status_updates"][-2:] == [
        (job.job_id, JobStatus.VERIFYING),
        (job.job_id, JobStatus.VERIFIED),
    ]
    python_artifacts = [
        a for a in test_store["artifacts"].values()
        if a.job_id == job.job_id and a.artifact_type == ArtifactType.PYTHON_FILE
    ]
    assert len(python_artifacts) == 1
    assert len(test_store["render_delay_payloads"]) == 1
    assert test_store["render_delay_payloads"][0]["job"]["job_id"] == str(job.job_id)


def test_verify_code_task_enqueues_fix_on_first_dry_run_failure(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_paths,
    test_store,
):
    # Given
    from app.workers import worker as worker_module
    from app.workers import worker_helpers

    monkeypatch.setattr(worker_helpers, "verify_code", lambda code, code_path: None)
    monkeypatch.setattr(
        worker_module, "dry_run_docker",
        lambda code_path, media_dir: (
            False,
            "Traceback (most recent call last):\nIndexError",
            True,
        ),
    )

    enqueued_fix = []
    monkeypatch.setattr(
        worker_module.fix_code_task, "delay", lambda payload: enqueued_fix.append(payload)
    )

    job = Job(status=JobStatus.CODED)
    test_store["jobs"][job.job_id] = job
    payload = JobCodeRequest(
        job=Job(job_id=job.job_id, status=JobStatus.CODED),
        code="from manim import *\n",
        is_retry=False,
    ).model_dump(mode="json")

    # When
    worker_module.verify_code_task(payload)

    # Then
    assert test_store["jobs"][job.job_id].status == JobStatus.FIXING
    assert len(enqueued_fix) == 1
    assert "IndexError" in enqueued_fix[0]["error_context"]


def test_verify_code_task_sets_failed_verification_on_second_dry_run_failure(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_paths,
    test_store,
):
    # Given
    from app.workers import worker as worker_module
    from app.workers import worker_helpers

    monkeypatch.setattr(worker_helpers, "verify_code", lambda code, code_path: None)
    monkeypatch.setattr(
        worker_module, "dry_run_docker",
        lambda code_path, media_dir: (False, "Traceback: IndexError", True),
    )

    job = Job(status=JobStatus.FIXING)
    test_store["jobs"][job.job_id] = job
    payload = JobCodeRequest(
        job=Job(job_id=job.job_id, status=JobStatus.FIXING),
        code="from manim import *\n",
        is_retry=True,
    ).model_dump(mode="json")

    # When
    worker_module.verify_code_task(payload)

    # Then
    assert test_store["jobs"][job.job_id].status == JobStatus.FAILED_VERIFICATION


def test_verify_code_task_enqueues_fix_on_first_static_analysis_failure(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    test_store,
):
    # Given
    from app.workers import worker as worker_module
    from app.workers import worker_helpers

    monkeypatch.setattr(
        worker_helpers, "verify_code",
        lambda code, code_path: "Forbidden imports: os",
    )

    enqueued_fix = []
    monkeypatch.setattr(
        worker_module.fix_code_task, "delay", lambda payload: enqueued_fix.append(payload)
    )

    job = Job(status=JobStatus.CODED)
    test_store["jobs"][job.job_id] = job
    payload = JobCodeRequest(
        job=Job(job_id=job.job_id, status=JobStatus.CODED),
        code="import os\nfrom manim import *\n",
        is_retry=False,
    ).model_dump(mode="json")

    # When
    worker_module.verify_code_task(payload)

    # Then
    assert test_store["jobs"][job.job_id].status == JobStatus.FIXING
    assert len(enqueued_fix) == 1
    assert "Forbidden imports" in enqueued_fix[0]["error_context"]


def test_verify_code_task_sets_failed_verification_on_second_static_failure(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    test_store,
):
    # Given
    from app.workers import worker as worker_module
    from app.workers import worker_helpers

    monkeypatch.setattr(
        worker_helpers, "verify_code",
        lambda code, code_path: "mypy errors: bad type",
    )

    job = Job(status=JobStatus.FIXING)
    test_store["jobs"][job.job_id] = job
    payload = JobCodeRequest(
        job=Job(job_id=job.job_id, status=JobStatus.FIXING),
        code="from manim import *\n",
        is_retry=True,
    ).model_dump(mode="json")

    # When
    worker_module.verify_code_task(payload)

    # Then
    assert test_store["jobs"][job.job_id].status == JobStatus.FAILED_VERIFICATION


def test_verify_code_task_does_not_persist_artifact_when_verification_fails(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    test_store,
):
    # Given — code that fails static analysis should never be saved
    from app.workers import worker as worker_module
    from app.workers import worker_helpers

    monkeypatch.setattr(
        worker_helpers, "verify_code",
        lambda code, code_path: "mypy errors: bad type",
    )
    monkeypatch.setattr(worker_module.fix_code_task, "delay", lambda payload: None)

    job = Job(status=JobStatus.CODED)
    test_store["jobs"][job.job_id] = job
    payload = JobCodeRequest(
        job=Job(job_id=job.job_id, status=JobStatus.CODED),
        code="from manim import *\n",
        is_retry=False,
    ).model_dump(mode="json")

    # When
    worker_module.verify_code_task(payload)

    # Then
    job_artifacts = [a for a in test_store["artifacts"].values() if a.job_id == job.job_id]
    assert len(job_artifacts) == 0, "Failed verification must not persist any artifact"


# ─────────────────────────────────────────────────────────────────────────────
# fix_code_task
# ─────────────────────────────────────────────────────────────────────────────

def test_fix_code_task_enqueues_re_verify_with_retry_flag_on_success(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_budget,
    test_store,
):
    # Given
    from app.workers import worker as worker_module

    fixed_code = (
        "from manim import *\n\n"
        "class Scene1(Scene):\n"
        "    def construct(self):\n"
        "        self.wait()\n"
    )
    monkeypatch.setattr(
        worker_module.LLMService, "render_fix_prompt",
        staticmethod(lambda code, error_context: ("fix-system-prompt", "fix-user-query")),
    )
    monkeypatch.setattr(
        worker_module.LLMService, "fix_call",
        staticmethod(lambda system_prompt, user_query: (fixed_code, 150)),
    )

    enqueued_verify = []
    monkeypatch.setattr(
        worker_module.verify_code_task, "delay", lambda payload: enqueued_verify.append(payload)
    )

    job = Job(status=JobStatus.FIXING)
    test_store["jobs"][job.job_id] = job
    payload = JobFixRequest(
        job=Job(job_id=job.job_id, status=JobStatus.FIXING),
        code="from manim import *\n",
        error_context="IndexError: list index out of range",
    ).model_dump(mode="json")

    # When
    worker_module.fix_code_task(payload)

    # Then
    assert len(enqueued_verify) == 1
    assert enqueued_verify[0]["is_retry"] is True
    assert enqueued_verify[0]["job"]["status"] == JobStatus.FIXING.value
    assert enqueued_verify[0]["code"] == fixed_code


def test_fix_code_task_sets_failed_verification_and_reraises_on_llm_error(
    monkeypatch,
    mock_repositories,
    mock_worker_cursor,
    mock_worker_budget,
    test_store,
):
    # Given
    from app.workers import worker as worker_module

    monkeypatch.setattr(
        worker_module.LLMService, "render_fix_prompt",
        staticmethod(lambda code, error_context: ("fix-system-prompt", "fix-user-query")),
    )
    monkeypatch.setattr(
        worker_module.LLMService, "fix_call",
        staticmethod(lambda sp, uq: (_ for _ in ()).throw(RuntimeError("LLM fix failed"))),
    )

    job = Job(status=JobStatus.FIXING)
    test_store["jobs"][job.job_id] = job
    payload = JobFixRequest(
        job=Job(job_id=job.job_id, status=JobStatus.FIXING),
        code="from manim import *\n",
        error_context="some error",
    ).model_dump(mode="json")

    # When / Then
    with pytest.raises(RuntimeError, match="LLM fix failed"):
        worker_module.fix_code_task(payload)

    assert test_store["jobs"][job.job_id].status == JobStatus.FAILED_VERIFICATION


# ─────────────────────────────────────────────────────────────────────────────
# generate_render — helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_render_payload(job, sample_video_plan, test_store):
    """Populate test_store with plan + code artifact, return serialised JobRequest."""
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


# ─────────────────────────────────────────────────────────────────────────────
# generate_render
# ─────────────────────────────────────────────────────────────────────────────

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

    # Docker security constraints enforced
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
    # Deliberately no plan in test_store
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
    # Deliberately no artifacts
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
