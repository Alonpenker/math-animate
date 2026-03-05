from typing import Optional
from pathlib import Path
from uuid import uuid4
import hashlib
import ast
import subprocess
import shutil
import os

from celery import current_task

from app.configs.app_settings import settings
from app.configs.llm_settings import LLM_PROVIDER
from app.dependencies.db import get_worker_cursor
from app.dependencies.redis_client import get_worker_redis
from app.dependencies.storage import get_storage_client
from app.domain.job_state import JobStatus, require_transition
from app.repositories.jobs_repository import JobsRepository
from app.repositories.artifacts_repository import ArtifactsRepository
from app.schemas.artifact import Artifact, ArtifactType
from app.services.budget_service import BudgetService
from app.services.files_storage_service import FilesStorageService
from app.workers.worker_settings import ALLOWED_IMPORTS, DANGEROUS_BUILTINS, PathNames, DockerCommands
from app.utils.logging import get_logger

logger = get_logger(__name__)


def log_context(job_id: Optional[str] = None) -> str:
    parts: list[str] = [f"pid={os.getpid()}"]
    if current_task is not None and getattr(current_task, "request", None) is not None:
        hostname = getattr(current_task.request, "hostname", None)
        if hostname:
            parts.append(f"worker={hostname}")
    if job_id:
        parts.append(f"job_id={job_id}")
    return " ".join(parts)


def transition_job(job_id, from_status: JobStatus, to_status: JobStatus) -> None:
    require_transition(from_status, to_status)
    with get_worker_redis() as redis_client:
        JobsRepository.update_job_status(redis_client, job_id, to_status)


def reserve_budget(call_id, job_id, stage: str, model: str, prompt_text: str) -> int:
    with get_worker_cursor() as cursor:
        return BudgetService.reserve(
            cursor, call_id, job_id, stage, LLM_PROVIDER, model, prompt_text
        )


def reconcile_budget(call_id, total_tokens: int) -> None:
    with get_worker_cursor() as cursor:
        BudgetService.reconcile(cursor, call_id, total_tokens)


def release_budget_on_error(call_id, reserved: int, total_tokens: int) -> None:
    if reserved:
        with get_worker_cursor() as cursor:
            BudgetService.release_on_error(cursor, call_id, max(reserved, total_tokens))


def get_storage() -> FilesStorageService:
    return FilesStorageService(client=get_storage_client(), bucket=settings.storage_bucket)


def save_artifact_to_storage(
    job_id,
    file_path: Path,
    artifact_type: ArtifactType,
    storage: FilesStorageService,
) -> None:
    file_bytes = file_path.read_bytes()
    object_path = storage.save_artifact(job_id, file_path)
    artifact = Artifact(
        artifact_id=uuid4(),
        job_id=job_id,
        artifact_type=artifact_type,
        path=object_path,
        size=len(file_bytes),
        sha256=hashlib.sha256(file_bytes).hexdigest(),
    )
    with get_worker_cursor() as cursor:
        ArtifactsRepository.create_artifact(cursor, artifact)


def verify_code(code: str, code_path: Path) -> str | None:
    """Run mypy type-check and AST safety analysis on generated code.

    Returns a failure reason string, or None if all checks pass.
    """

    # --- Part A: mypy check ---
    try:
        result = subprocess.run(
            ["mypy",
            "--ignore-missing-imports",
            "--follow-imports=skip",
            "--disable-error-code=name-defined",
            "--disable-error-code=attr-defined",
            str(code_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return f"mypy errors:\n{result.stdout}{result.stderr}"
    except Exception as exc:
        return f"mypy check failed with exception: {exc}"

    # --- Part B: AST import & dangerous-builtin analysis ---
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return f"AST parse syntax error: {exc}"

    forbidden_imports: list[str] = []
    dangerous_calls: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top_module = alias.name.split(".")[0]
                if top_module not in ALLOWED_IMPORTS:
                    forbidden_imports.append(top_module)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top_module = node.module.split(".")[0]
                if top_module not in ALLOWED_IMPORTS:
                    forbidden_imports.append(top_module)

        if isinstance(node, ast.Call):
            func = node.func
            name: str | None = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name and name in DANGEROUS_BUILTINS:
                dangerous_calls.append(name)

    if forbidden_imports:
        return f"Forbidden imports: {', '.join(sorted(set(forbidden_imports)))}"
    if dangerous_calls:
        return f"Dangerous builtin calls: {', '.join(sorted(set(dangerous_calls)))}"

    return None


def extract_traceback(stderr: str) -> str:
    """Extract the traceback portion from stderr output.

    If a "Traceback (most recent call last)" marker is found, returns everything
    from the first occurrence to the end. Otherwise returns the full stderr as-is.
    """
    marker = "Traceback (most recent call last)"
    idx = stderr.find(marker)
    if idx != -1:
        return stderr[idx:]
    return stderr


def dry_run_docker(code_path: Path, media_dir: Path) -> tuple[bool, str, bool]:
    """Run ``manim --dry_run`` inside Docker to verify generated code.

    Returns (passed, error_message, is_fixable).
    is_fixable=True means the error came from the generated Manim code itself
    and is worth sending to the fix step. is_fixable=False means it's an
    infrastructure problem (timeout, Docker failure) unrelated to the code.
    """
    render_root = Path(PathNames.TMP_RENDER_FOLDER)

    command = [
        *DockerCommands.BIN,
        *DockerCommands.INTERACTIVE,
        *DockerCommands.NETWORK,
        *DockerCommands.CPU,
        *DockerCommands.MEMORY,
        *DockerCommands.PIDS,
        *DockerCommands.SECURITY,
        *DockerCommands.volume(str(render_root), render_root, "rw"),
        *DockerCommands.IMAGE,
        *DockerCommands.manim_dry_run_command(code_path, media_dir),
    ]

    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=60, input="*\n",
        )
        if result.returncode == 0:
            return True, "", True
        error_output = (result.stdout or "") + (result.stderr or "")
        return False, extract_traceback(error_output), True
    except subprocess.TimeoutExpired:
        return False, "Dry-run timed out after 60s.", False
    except Exception as exc:
        return False, str(exc), False


def store_render_logs(
    storage: FilesStorageService,
    job_id,
    stdout_content: str,
    stderr_content: str,
) -> None:
    """Best-effort storage of render stdout/stderr as LOG artifacts."""
    job_dir = Path(PathNames.ARTIFACTS_FOLDER) / str(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)

    for filename, content in [
        ("render_stdout.log", stdout_content),
        ("render_stderr.log", stderr_content),
    ]:
        file_path = job_dir / filename
        try:
            file_path.write_bytes(content.encode("utf-8"))
            save_artifact_to_storage(job_id, file_path, ArtifactType.LOG, storage)
        except Exception:
            logger.warning(
                "Failed to store %s artifact (%s)",
                filename, log_context(str(job_id)),
                exc_info=True,
            )
        finally:
            file_path.unlink(missing_ok=True)
    shutil.rmtree(job_dir, ignore_errors=True)
