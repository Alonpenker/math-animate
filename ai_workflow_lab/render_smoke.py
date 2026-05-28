from pathlib import Path

from settings import RUNS_DIR, LogFileNames, PathNames, RunFolderNames
from verify_render import dry_run_docker, render_docker, summarize_verification_failure


SMOKE_CODE = """from manim import *


class Scene1(Scene):
    def construct(self):
        title = Text("Smoke Scene 1", font_size=42)
        square = Square(color=BLUE).next_to(title, DOWN, buff=0.6)
        self.play(Write(title))
        self.play(Create(square))
        self.wait(0.5)


class Scene2(Scene):
    def construct(self):
        title = Text("Smoke Scene 2", font_size=42)
        circle = Circle(color=GREEN).next_to(title, DOWN, buff=0.6)
        self.play(Write(title))
        self.play(Create(circle))
        self.wait(0.5)
"""


def main() -> None:
    run_dir = RUNS_DIR / "smoke"
    code_dir = run_dir / RunFolderNames.ATTEMPTS / "0"
    media_dir = run_dir / RunFolderNames.MEDIA
    logs_dir = run_dir / RunFolderNames.LOGS
    for path in (code_dir, media_dir, logs_dir):
        path.mkdir(parents=True, exist_ok=True)

    code_path = code_dir / PathNames.MANIM_CODE
    code_path.write_text(SMOKE_CODE, encoding="utf-8")
    print(f"Smoke code: {code_path}", flush=True)

    passed, error_output, is_fixable, stdout, stderr = dry_run_docker(
        code_path=code_path,
        media_dir=code_dir / RunFolderNames.DRY_RUN_MEDIA,
        run_dir=run_dir,
    )
    (logs_dir / LogFileNames.SMOKE_DRY_RUN_STDOUT).write_text(stdout, encoding="utf-8")
    (logs_dir / LogFileNames.SMOKE_DRY_RUN_STDERR).write_text(stderr, encoding="utf-8")
    if not passed:
        print("Dry-run failed.", flush=True)
        print(f"is_fixable={is_fixable}", flush=True)
        print(summarize_verification_failure(error_output), flush=True)
        raise SystemExit(1)
    print("Dry-run passed.", flush=True)

    output_files, stdout, stderr = render_docker(
        code_path=code_path,
        media_dir=media_dir,
        run_dir=run_dir,
        expected_scene_count=2,
    )
    (logs_dir / LogFileNames.SMOKE_RENDER_STDOUT).write_text(stdout, encoding="utf-8")
    (logs_dir / LogFileNames.SMOKE_RENDER_STDERR).write_text(stderr, encoding="utf-8")
    print("Render passed.", flush=True)
    for output_file in output_files:
        print(output_file, flush=True)


if __name__ == "__main__":
    main()
