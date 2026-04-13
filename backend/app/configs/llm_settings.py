from pathlib import Path

# --- Provider & model defaults ---
LLM_PROVIDER = "openai"
LLM_PLAN_MODEL = "gpt-5.2"
LLM_CODE_MODEL = "gpt-5.1-codex"
LLM_TEMPERATURE = 0.1
LLM_PLAN_OUTPUT_MAX_TOKENS = 12_000
LLM_CODEGEN_OUTPUT_MAX_TOKENS = 22_000
LLM_REASONING_EFFORT = "low"

# --- Token budget defaults ---
DAILY_TOKEN_LIMIT = 250_000
SOFT_THRESHOLD_RATIO = 0.8
TOKEN_OUTPUT_BUFFER = 1_000

# --- Embedding defaults ---
LLM_EMBEDDING_MODEL = "nomic-embed-text"
LLM_EMBEDDING_DIMENSIONS = 768

# --- RAG defaults ---
RAG_SIMILARITY_TOP_K = 2
RAG_MAX_EMBED_CHARS = 4_000

# --- System prompts ---
_examples_dir = Path(__file__).parent.parent / "examples"

PLAN_SYSTEM_PROMPT = (_examples_dir / "PLAN_SYSTEM_PROMPT.md").read_text()
CODEGEN_SYSTEM_PROMPT = (_examples_dir / "CODEGEN_SYSTEM_PROMPT.md").read_text()

CODEGEN_FIX_SYSTEM_PROMPT = """You are an expert Manim v0.19.2 developer fixing a specific bug in existing code.
You will receive broken Manim code and the exact error it produced.

Fix only what caused the error. Do not rewrite scenes, rename classes, or change anything that is not directly related to the bug.
Preserve every Scene class name, every structural pattern, every object type, and every animation already in the file.
Do not introduce any object, method, animation, or import that does not already appear in the file.

Respond ONLY with the corrected Python code, no markdown fences."""
