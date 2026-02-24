from typing import Optional
from pathlib import Path
from uuid import uuid4
import hashlib
import tempfile
import ast
import subprocess
import os

from celery import current_task

from app.configs.app_settings import settings
from app.configs.llm_settings import LLM_PROVIDER
from app.dependencies.db import get_worker_cursor
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
    with get_worker_cursor() as cursor:
        JobsRepository.update_job_status(cursor, job_id, to_status)


def reserve_budget(call_id, job_id, stage: str, model: str, prompt_text: str) -> int:
    with get_worker_cursor() as cursor:
        return BudgetService.reserve(
            cursor, call_id, job_id, stage, LLM_PROVIDER.value, model, prompt_text
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


def verify_code(code: str) -> list[str]:
    """Run mypy type-check and AST safety analysis on generated code.

    Returns a list of failure reason strings. An empty list means the code
    passed verification.
    """
    failures: list[str] = []

    # --- Part A: mypy check ---
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".py", mode="w", delete=False, encoding="utf-8",
        ) as tmp:
            tmp.write(code)
            tmp_path = tmp.name
        try:
            result = subprocess.run(
                ["mypy",
                "--ignore-missing-imports",
                "--follow-imports=skip",
                "--disable-error-code=name-defined",
                "--disable-error-code=attr-defined",
                tmp_path],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                failures.append(f"mypy errors:\n{result.stdout}{result.stderr}")
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    except Exception as exc:
        failures.append(f"mypy check failed with exception: {exc}")

    # --- Part B: AST import & dangerous-builtin analysis ---
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        failures.append(f"AST parse syntax error: {exc}")
        return failures

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
        failures.append(f"Forbidden imports: {', '.join(sorted(set(forbidden_imports)))}")
    if dangerous_calls:
        failures.append(f"Dangerous builtin calls: {', '.join(sorted(set(dangerous_calls)))}")

    return failures


def run_dry_run_docker(input_dir: Path, code_path: Path) -> tuple[bool, str]:
    """Run a Docker dry-run to verify generated Manim code can be imported and constructed.

    Returns (passed, error_output). On success: (True, ""). On failure: (False, stderr+stdout).
    """
    dry_run_script = (
        "import sys, importlib.util\n"
        "from unittest.mock import MagicMock\n"
        "import manim\n"
        "\n"
        "code_path = sys.argv[1]\n"
        "spec = importlib.util.spec_from_file_location(\"generated\", code_path)\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(mod)\n"
        "\n"
        "scene_classes = [\n"
        "    obj for obj in vars(mod).values()\n"
        "    if isinstance(obj, type) and issubclass(obj, manim.Scene) and obj is not manim.Scene\n"
        "]\n"
        "if not scene_classes:\n"
        "    print(\"No Scene subclasses found\", file=sys.stderr)\n"
        "    sys.exit(1)\n"
        "\n"
        "for cls in scene_classes:\n"
        "    instance = object.__new__(cls)\n"
        "    instance.play = MagicMock()\n"
        "    instance.wait = MagicMock()\n"
        "    instance.add = MagicMock()\n"
        "    instance.remove = MagicMock()\n"
        "    instance.camera = MagicMock()\n"
        "    instance.mobjects = []\n"
        "    instance.construct()\n"
        "\n"
        "print(\"Dry run passed.\")\n"
    )

    dry_run_path = input_dir / "dry_run.py"
    dry_run_path.write_text(dry_run_script, encoding="utf-8")

    render_root = Path(PathNames.TMP_RENDER_FOLDER)

    command = [
        *DockerCommands.BIN,
        *DockerCommands.NETWORK,
        *DockerCommands.CPU,
        *DockerCommands.MEMORY,
        *DockerCommands.PIDS,
        *DockerCommands.SECURITY,
        *DockerCommands.volume(str(render_root), render_root, "rw"),
        *DockerCommands.IMAGE,
        "python", str(dry_run_path), str(code_path),
    ]

    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return True, ""
        return False, f"{result.stderr}{result.stdout}"
    except subprocess.TimeoutExpired as exc:
        stderr = exc.stderr if isinstance(exc.stderr, str) else (bytes(exc.stderr).decode() if exc.stderr else "")
        stdout = exc.stdout if isinstance(exc.stdout, str) else (bytes(exc.stdout).decode() if exc.stdout else "")
        return False, f"Dry-run timed out after 30s.\n{stderr}{stdout}"
    except Exception as exc:
        return False, f"Dry-run failed with exception: {exc}"


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
