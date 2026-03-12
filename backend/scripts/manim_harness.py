"""Standalone Manim iteration harness.

Runs every .py file found in ``scripts/inputs/`` through the exact same Docker
invocation the production worker uses (full render, ``-qh -a``,
``manimcommunity/manim:v0.19.2``, identical security flags).

Usage:
    uv run python scripts/manim_harness.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so we can import worker_settings.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.workers.worker_settings import DockerCommands, PathNames, RENDER_TIMEOUT_SECONDS

SCRIPTS_DIR = Path(__file__).resolve().parent
INPUTS_DIR = SCRIPTS_DIR / "inputs"
OUTPUTS_DIR = SCRIPTS_DIR / "outputs"

TRACEBACK_MARKER = "Traceback (most recent call last)"


def _decode_output(data: bytes | bytearray | memoryview | str | None) -> str:
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    return bytes(data).decode("utf-8", errors="replace")


def _extract_traceback(stderr: str) -> str:
    idx = stderr.find(TRACEBACK_MARKER)
    if idx != -1:
        return stderr[idx:]
    return stderr


def run_single(py_file: Path) -> tuple[str, str]:
    """Render a single .py file and return (status, error_detail)."""
    stem = py_file.stem
    output_dir = OUTPUTS_DIR / stem
    if output_dir.exists():
        return "SKIP", ""
    output_dir.mkdir(parents=True, exist_ok=True)

    code_dest = output_dir / py_file.name
    shutil.copy2(py_file, code_dest)

    media_dir = output_dir / PathNames.MEDIA_FOLDER
    media_dir.mkdir(parents=True, exist_ok=True)

    container_root = PathNames.TMP_RENDER_FOLDER
    container_code = f"{container_root}/{py_file.name}"
    container_media = f"{container_root}/{PathNames.MEDIA_FOLDER}"

    command = [
        *DockerCommands.BIN,
        *DockerCommands.NETWORK,
        *DockerCommands.CPU,
        *DockerCommands.MEMORY,
        *DockerCommands.PIDS,
        *DockerCommands.SECURITY,
        *DockerCommands.volume(str(output_dir), container_root, "rw"),
        *DockerCommands.IMAGE,
        *DockerCommands.manim_command(code_path=container_code, media_dir=container_media),
    ]

    try:
        result = subprocess.run(
            command, capture_output=True, timeout=RENDER_TIMEOUT_SECONDS,
        )
        stdout_text = _decode_output(result.stdout)
        stderr_text = _decode_output(result.stderr)
    except subprocess.TimeoutExpired as exc:
        stdout_text = _decode_output(exc.stdout)
        stderr_text = _decode_output(exc.stderr)
        stderr_text = f"Render timed out after {RENDER_TIMEOUT_SECONDS}s.\n{stderr_text}"
        result = None

    (output_dir / "render_stdout.txt").write_text(stdout_text, encoding="utf-8")
    (output_dir / "render_stderr.txt").write_text(stderr_text, encoding="utf-8")

    if result is not None and result.returncode == 0:
        (output_dir / "result.txt").write_text("PASS", encoding="utf-8")
        return "PASS", ""

    traceback_text = _extract_traceback(stderr_text)
    (output_dir / "result.txt").write_text(f"FAIL: {traceback_text}", encoding="utf-8")
    return "FAIL", traceback_text


def main() -> None:
    if not INPUTS_DIR.exists():
        print(f"Directory does not exist: {INPUTS_DIR}")
        return
    
    py_files = sorted(INPUTS_DIR.glob("*.py"))
    if not py_files:
        print(f"No .py files found in {INPUTS_DIR}")
        return

    results: list[tuple[str, str]] = []
    for py_file in py_files:
        print(f"--- Running: {py_file.name} ---")
        status, error = run_single(py_file)
        results.append((py_file.name, status))
        print(f"\tResult: {status}")
        if error:
            first_line = error.split("\n")[0]
            print(f"\tError:  {first_line}")
        print()

    pass_count = sum(1 for _, status in results if status == "PASS")
    fail_count = sum(1 for _, status in results if status == "FAIL")
    skip_count = sum(1 for _, status in results if status == "SKIP")
    lines = [
        f"Total: {len(results)}  Pass: {pass_count}  Fail: {fail_count}  Skip: {skip_count}",
        "",
    ]
    for name, status in results:
        lines.append(f"  {status}  {name}")
    lines.append("")

    summary = "\n".join(lines)
    print(summary)


if __name__ == "__main__":
    main()
