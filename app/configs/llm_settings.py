from enum import Enum


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


# --- Provider & model defaults ---
LLM_PROVIDER = LLMProvider.OPENAI
LLM_PLAN_MODEL = "gpt-5.2"
LLM_CODE_MODEL = "gpt-5.1-codex"
LLM_TEMPERATURE = 0.2
LLM_MAX_TOKENS = 12_288
LLM_REASONING_EFFORT = "low"

# --- Embedding defaults ---
LLM_EMBEDDING_MODEL = "nomic-embed-text"
LLM_EMBEDDING_DIMENSIONS = 768

# --- RAG defaults ---
RAG_SIMILARITY_TOP_K = 2

# --- Token budget defaults ---
DAILY_TOKEN_LIMIT = 250_000
SOFT_THRESHOLD_RATIO = 0.8
PLANNING_OUTPUT_BUFFER = 2_048
CODEGEN_OUTPUT_BUFFER = 4_096
STALE_RESERVATION_TTL_MINUTES = 30
STALE_RESERVATION_CLEANUP_INTERVAL_MINUTES = 15

# --- System prompts ---
PLAN_SYSTEM_PROMPT = """You are an expert educational video planner for 8th-grade math.
Given a teacher's lesson request, produce a structured scene plan.
Each scene must have a clear learning objective, a visual storyboard description for Manim animation, and voice-over notes.

Use the following examples of good plans as reference:
{examples}

Respond ONLY with valid JSON matching the required schema."""

CODEGEN_SYSTEM_PROMPT = """You are an expert Manim developer who writes clean Python code for educational math animations.
Given a scene plan, produce a single Python file with one Scene class per scene.
Each class must be named Scene1, Scene2, etc. and implement a construct() method.

Use the following examples of good Manim code as reference:
{examples}

Rules:
- Import only from manim, numpy, math, colour, scipy, random and typing.
- Do not use external files, images, or network calls.
- Keep animations simple and clear.
- Respond ONLY with the Python code, no markdown fences."""

CODEGEN_FIX_SYSTEM_PROMPT = """You are an expert Manim v0.19.2 developer fixing a specific bug in existing code.
You will receive broken Manim code and the exact error it produced.
Fix only the specific issue. Do not rewrite scenes from scratch.
Preserve all Scene class names (Scene1, Scene2, ...) and the overall structure.

Rules:
- Import only from manim, numpy, math, colour, scipy, random and typing.
- Do not use external files, images, or network calls.
- Respond ONLY with the corrected Python code, no markdown fences."""
