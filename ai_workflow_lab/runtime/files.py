import json
import shutil
from datetime import datetime
from pathlib import Path

from schemas import CodePlan, VideoPlan
from settings import (
    E2E_RUN_NAME,
    PROMPTS_DIR,
    RUNS_DIR,
    VISUAL_KIT_SOURCE,
    PathNames,
    RunFileNames,
    RunFolderNames,
)


class RunFiles:
    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir

    @classmethod
    def create(cls, name: str | None, *, overwrite: bool = False) -> "RunFiles":
        run_name = name or datetime.now().strftime("%Y%m%d-%H%M%S")
        if overwrite and run_name != E2E_RUN_NAME:
            raise ValueError("Run overwrite is only allowed for the e2e run.")
        run_dir = RUNS_DIR / run_name
        if run_dir.exists():
            if overwrite:
                shutil.rmtree(run_dir)
            else:
                raise FileExistsError(
                    f"Run folder already exists: {run_dir}. Choose a new --name."
                )
        run_dir.mkdir(parents=True)
        files = cls(run_dir)
        files.ensure_layout()
        return files

    @property
    def logs_dir(self) -> Path:
        return self.run_dir / RunFolderNames.LOGS

    @property
    def media_dir(self) -> Path:
        return self.run_dir / RunFolderNames.MEDIA

    @property
    def prompts_dir(self) -> Path:
        return self.run_dir / RunFolderNames.PROMPTS

    def ensure_layout(self) -> None:
        for folder in (
            RunFolderNames.ATTEMPTS,
            RunFolderNames.FINAL,
            RunFolderNames.LOGS,
            RunFolderNames.MEDIA,
            RunFolderNames.PROMPTS,
        ):
            (self.run_dir / folder).mkdir(parents=True, exist_ok=True)

    def write_request(self, request_text: str) -> None:
        self.write_text(self.run_dir / RunFileNames.REQUEST, request_text + "\n")

    def read_prompt(self, filename: str) -> str:
        return (PROMPTS_DIR / filename).read_text(encoding="utf-8")

    def archive_prompt_file(self, source_filename: str, target_filename: str) -> None:
        self.write_text(self.prompts_dir / target_filename, self.read_prompt(source_filename))

    def write_prompt(self, filename: str, content: str) -> None:
        text = content if content.endswith("\n") else content + "\n"
        self.write_text(self.prompts_dir / filename, text)

    def save_plan(self, plan: VideoPlan) -> None:
        self.write_text(self.run_dir / RunFileNames.PLAN, plan.to_prompt_text())

    def save_code_plan(self, code_plan: CodePlan) -> None:
        self.write_text(
            self.run_dir / RunFileNames.CODE_PLAN,
            code_plan.to_prompt_text(),
        )

    def write_selected_documents(self, metadata: dict) -> None:
        self.write_json(self.run_dir / RunFileNames.SELECTED_DOCUMENTS, metadata)

    def attempt_dir(self, attempt: int) -> Path:
        path = self.run_dir / RunFolderNames.ATTEMPTS / str(attempt)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_attempt_code(self, attempt: int, code: str) -> Path:
        path = self.attempt_dir(attempt) / PathNames.MANIM_CODE
        self.write_text(path, code)
        self.copy_visual_kit(path.parent)
        return path

    def dry_run_media_dir(self, attempt: int) -> Path:
        return self.attempt_dir(attempt) / RunFolderNames.DRY_RUN_MEDIA

    def write_log(self, filename: str, content: str) -> None:
        self.write_text(self.logs_dir / filename, content)

    def write_log_json(self, filename: str, data: object) -> None:
        self.write_json(self.logs_dir / filename, data)

    def append_log_line(self, filename: str, line: str) -> None:
        with (self.logs_dir / filename).open("a", encoding="utf-8") as handle:
            handle.write(line.rstrip() + "\n")

    def read_log_json(self, filename: str) -> dict | None:
        path = self.logs_dir / filename
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def save_final_code(self, code: str) -> Path:
        path = self.run_dir / RunFolderNames.FINAL / PathNames.MANIM_CODE
        self.write_text(path, code)
        self.copy_visual_kit(path.parent)
        return path

    def copy_visual_kit(self, target_dir: Path) -> Path:
        target = target_dir / PathNames.VISUAL_KIT
        shutil.copy2(VISUAL_KIT_SOURCE, target)
        return target

    def relative_paths(self, paths: list[Path]) -> list[str]:
        return [str(path.relative_to(self.run_dir)) for path in paths]

    def write_summary(self, data: dict, token_summary: dict | None) -> None:
        if token_summary and "token_usage" not in data:
            data = {**data, "token_usage": token_summary}
        self.write_json(self.run_dir / RunFileNames.SUMMARY, data)

    @staticmethod
    def write_text(path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")

    @staticmethod
    def write_json(path: Path, data: object) -> None:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
