import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
RUNS_DIR = ROOT_DIR / "runs"
PROMPTS_DIR = ROOT_DIR / "llm_knowledge" / "prompts"
VISUAL_KIT_SOURCE = ROOT_DIR / "llm_knowledge" / "manim_skill" / "visual_kit.py"
VISUAL_KIT_API = ROOT_DIR / "llm_knowledge" / "manim_skill" / "rules" / "visual-kit-api.md"
E2E_RUN_NAME = "e2e"


def load_env_file(path: Path = ROOT_DIR / ".env") -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file()


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_PLAN_MODEL = "openrouter/owl-alpha"
OPENROUTER_CODE_MODEL = "openai/gpt-oss-120b:free"
OPENROUTER_QA_MODEL = "openrouter/owl-alpha"
OPENROUTER_CODE_PLAN_MODEL = OPENROUTER_PLAN_MODEL
OPENROUTER_HTTP_REFERER = "http://localhost"
OPENROUTER_APP_TITLE = "AI Workflow Lab"


PLAN_OUTPUT_MAX_TOKENS = 4_000
CODE_PLAN_OUTPUT_MAX_TOKENS = 4_000
CODEGEN_OUTPUT_MAX_TOKENS = 8_000
CODE_QA_OUTPUT_MAX_TOKENS = 4_000
CODGEN_REASONING_EFFORT = "low"
FIX_REASONING_EFFORT = "medium"

MAX_ATTEMPTS = 3
DRY_RUN_TIMEOUT_SECONDS = 90
RENDER_TIMEOUT_SECONDS = 600

ALLOWED_IMPORTS: frozenset[str] = frozenset({
    "manim",
    "numpy",
    "math",
    "colour",
    "scipy",
    "random",
    "typing",
})

VISUAL_KIT_LAYOUT_TEMPLATES: frozenset[str] = frozenset({
    "center",
    "split",
})

DANGEROUS_BUILTINS: frozenset[str] = frozenset({
    "exec",
    "eval",
    "open",
    "__import__",
    "compile",
})

BASE_SELECTED_DOCUMENT_TITLES: tuple[str, ...] = (
    "Educational Storyboarding",
    "Animation Patterns",
    "Math Visual Clarity",
)

STATIC_DOCUMENT_SELECTION_PROFILES: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (
        ("pythagoras", "pythagorean", "right triangle", "hypotenuse"),
        (
            "Right Triangle Diagram Template",
            "Triangle Comparison Template",
            "Squares On Triangle Sides Template",
            "Pythagorean Area Template",
            "Geometry Shapes and Labels",
            "Equation Transitions",
        ),
    ),
    (
        ("derivative", "derivatives", "limit", "limits", "tangent line"),
        ("Derivatives From Limits", "Axes and Graphing", "Equation Transitions"),
    ),
    (
        ("function", "functions", "graph", "graphs", "transformation", "transformations"),
        ("Function Transformations", "Axes and Graphing"),
    ),
    (
        ("matrix", "matrices", "dot product", "linear algebra"),
        ("Matrix Multiplication", "Matrix Drawing Patterns"),
    ),
    (
        ("circle", "tangent", "construction", "compass"),
        (
            "External Circle Tangent Construction",
            "Geometry Shapes and Labels",
            "Lines, Arrows, and Labels",
        ),
    ),
)


class PathNames:
    MANIM_CODE = "code.py"
    MEDIA_FOLDER = "media"
    VIDEOS_FOLDER = "videos"
    RESOLUTION_FOLDER = "720p30"


class RunFolderNames:
    ATTEMPTS = "attempts"
    FINAL = "final"
    LOGS = "logs"
    MEDIA = PathNames.MEDIA_FOLDER
    PROMPTS = "prompts"
    DRY_RUN_MEDIA = "dry_run_media"


class RunFileNames:
    REQUEST = "request.txt"
    PLAN = "plan.txt"
    CODE_PLAN = "code_plan.json"
    SELECTED_DOCUMENTS = "selected_documents.json"
    SUMMARY = "summary.json"


class PromptFiles:
    PLAN_SYSTEM = "PLAN_SYSTEM_PROMPT.md"
    CODE_PLAN_SYSTEM = "CODE_PLAN_SYSTEM_PROMPT.md"
    CODEGEN_SYSTEM = "CODEGEN_SYSTEM_PROMPT.md"
    CODEGEN_FIX_SYSTEM = "CODEGEN_FIX_SYSTEM_PROMPT.md"
    CODE_QA_SYSTEM = "CODE_QA_SYSTEM_PROMPT.md"


class ArchivedPromptFiles:
    GENERATE_PLAN_SYSTEM = "generate_plan_system.md"
    GENERATE_PLAN_USER = "generate_plan_user.txt"
    GENERATE_CODE_PLAN_SYSTEM = "generate_code_plan_system.md"
    GENERATE_CODE_PLAN_USER = "generate_code_plan_user.txt"
    GENERATE_CODE_SYSTEM = "generate_code_system.md"
    GENERATE_CODE_USER = "generate_code_user.txt"
    CODE_QA_SYSTEM = "code_qa_system.md"
    FIX_SYSTEM = "fix_system.md"

    @staticmethod
    def fix_attempt_user(attempt: int) -> str:
        return f"fix_attempt_{attempt}_user.txt"

    @staticmethod
    def code_qa_attempt_user(attempt: int) -> str:
        return f"code_qa_attempt_{attempt}_user.txt"


class LogFileNames:
    WORKFLOW = "workflow.log"
    CODE_PLAN_VALIDATION_ERROR = "code_plan_validation_error.json"
    RENDER_STDOUT = "render_stdout.log"
    RENDER_STDERR = "render_stderr.log"

    @staticmethod
    def attempt_verify(attempt: int) -> str:
        return f"attempt_{attempt}_verify.log"

    @staticmethod
    def attempt_dry_run_stdout(attempt: int) -> str:
        return f"attempt_{attempt}_dry_run_stdout.log"

    @staticmethod
    def attempt_dry_run_stderr(attempt: int) -> str:
        return f"attempt_{attempt}_dry_run_stderr.log"

    @staticmethod
    def code_qa_attempt(attempt: int) -> str:
        return f"code_qa_attempt_{attempt}.json"


class UsageFileNames:
    GENERATE_PLAN = "generate_plan_usage.json"
    GENERATE_CODE_PLAN = "generate_code_plan_usage.json"
    GENERATE_CODE = "generate_code_usage.json"
    TOKEN_USAGE_JSONL = "token_usage.jsonl"
    TOKEN_USAGE_SUMMARY = "token_usage_summary.json"

    @staticmethod
    def fix_attempt(attempt: int) -> str:
        return f"fix_attempt_{attempt}_usage.json"

    @staticmethod
    def code_qa_attempt(attempt: int) -> str:
        return f"code_qa_attempt_{attempt}_usage.json"


class DockerCommands:
    BIN = ("docker", "run", "--rm")
    INTERACTIVE = ("-i",)
    NETWORK = ("--network", "none")
    CPU = ("--cpus", "1")
    MEMORY = ("--memory", "2g")
    PIDS = ("--pids-limit", "256")
    SECURITY = (
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
    )
    IMAGE = ("manimcommunity/manim:v0.19.2",)

    @staticmethod
    def volume(src: str | Path, dst: str | Path, mode: str) -> tuple[str, str]:
        return ("-v", f"{src}:{dst}:{mode}")
