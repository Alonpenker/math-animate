import ast
import re
import subprocess
from pathlib import Path, PurePosixPath

from settings import (
    ALLOWED_IMPORTS,
    DANGEROUS_BUILTINS,
    DRY_RUN_TIMEOUT_SECONDS,
    RENDER_TIMEOUT_SECONDS,
    DockerCommands,
    PathNames,
)


CONTAINER_RUN_DIR = PurePosixPath("/workspace")


def verify_code_static(code: str) -> str | None:
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
    marker = "Traceback (most recent call last)"
    index = stderr.find(marker)
    if index != -1:
        return stderr[index:]
    return stderr


def _decode_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return value.decode("utf-8", errors="replace")


def summarize_verification_failure(failure: str) -> str:
    lines = [line.strip() for line in failure.strip().splitlines() if line.strip()]
    if not lines:
        return failure

    exception_line = re.compile(r"\b[A-Za-z_][\w.]*(?:Error|Exception):")
    for index in range(len(lines) - 1, -1, -1):
        if exception_line.search(lines[index]):
            return " ".join(lines[index:])
    return lines[-1]


def _container_path(host_path: Path, run_dir: Path) -> PurePosixPath:
    relative = host_path.resolve().relative_to(run_dir.resolve())
    return CONTAINER_RUN_DIR.joinpath(*relative.parts)


def _is_infrastructure_failure(error_output: str) -> bool:
    normalized = error_output.replace("\\", "/")
    return (
        "FileNotFoundError:" in error_output
        and "/workspace/" in normalized
        and "code.py not found" in normalized
    )


def _prepare_writable_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(0o777)
    except OSError:
        pass


def dry_run_docker(
    *,
    code_path: Path,
    media_dir: Path,
    run_dir: Path,
) -> tuple[bool, str, bool, str, str]:
    _prepare_writable_dir(media_dir)
    container_code_path = _container_path(code_path, run_dir)
    container_media_dir = _container_path(media_dir, run_dir)
    command = [
        *DockerCommands.BIN,
        *DockerCommands.INTERACTIVE,
        *DockerCommands.NETWORK,
        *DockerCommands.CPU,
        *DockerCommands.MEMORY,
        *DockerCommands.PIDS,
        *DockerCommands.SECURITY,
        *DockerCommands.volume(run_dir.resolve(), CONTAINER_RUN_DIR, "rw"),
        *DockerCommands.IMAGE,
        "manim",
        "-ql",
        "-a",
        "--dry_run",
        "--media_dir",
        str(container_media_dir),
        str(container_code_path),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            timeout=DRY_RUN_TIMEOUT_SECONDS,
            input=b"*\n",
        )
        stdout, stderr = _decode_output(result.stdout), _decode_output(result.stderr)
        if result.returncode == 0:
            return True, "", True, stdout, stderr
        if result.returncode in {125, 126, 127}:
            return False, extract_traceback(stdout + stderr), False, stdout, stderr
        error_output = extract_traceback(stdout + stderr)
        return False, error_output, not _is_infrastructure_failure(error_output), stdout, stderr
    except subprocess.TimeoutExpired as exc:
        stdout = _decode_output(exc.stdout)
        stderr = _decode_output(exc.stderr)
        return (
            False,
            f"Dry-run timed out after {DRY_RUN_TIMEOUT_SECONDS}s.",
            False,
            stdout,
            stderr,
        )
    except Exception as exc:
        return False, str(exc), False, "", ""


def render_docker(
    *,
    code_path: Path,
    media_dir: Path,
    run_dir: Path,
    expected_scene_count: int,
) -> tuple[list[Path], str, str]:
    _prepare_writable_dir(media_dir)
    container_code_path = _container_path(code_path, run_dir)
    container_media_dir = _container_path(media_dir, run_dir)
    command = [
        *DockerCommands.BIN,
        *DockerCommands.NETWORK,
        *DockerCommands.CPU,
        *DockerCommands.MEMORY,
        *DockerCommands.PIDS,
        *DockerCommands.SECURITY,
        *DockerCommands.volume(run_dir.resolve(), CONTAINER_RUN_DIR, "rw"),
        *DockerCommands.IMAGE,
        "manim",
        "-qm",
        "-a",
        "--media_dir",
        str(container_media_dir),
        str(container_code_path),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            timeout=RENDER_TIMEOUT_SECONDS,
        )
        stdout, stderr = _decode_output(result.stdout), _decode_output(result.stderr)
        if result.returncode != 0:
            raise RuntimeError(
                f"Docker render exited with code {result.returncode}.\n"
                f"{extract_traceback(stdout + stderr)}"
            )
    except subprocess.TimeoutExpired as exc:
        stdout = _decode_output(exc.stdout)
        stderr = _decode_output(exc.stderr)
        raise RuntimeError(f"Render timed out after {RENDER_TIMEOUT_SECONDS}s.") from exc

    videos_dir = (
        media_dir
        / PathNames.VIDEOS_FOLDER
        / code_path.stem
        / PathNames.RESOLUTION_FOLDER
    )
    if not videos_dir.exists():
        raise RuntimeError(f"Render output folder not found: {videos_dir}")

    output_files = sorted(p for p in videos_dir.glob("*.mp4") if p.is_file())
    if len(output_files) != expected_scene_count:
        raise RuntimeError(
            f"Render output count mismatch: expected {expected_scene_count} mp4 files, "
            f"got {len(output_files)}."
        )
    return output_files, stdout, stderr
