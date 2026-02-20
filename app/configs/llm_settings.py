from enum import Enum


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


# --- Provider & model defaults ---
LLM_PROVIDER = LLMProvider.OPENAI
LLM_PLAN_MODEL = "gpt-5.2"
LLM_CODE_MODEL = "gpt-5.1-codex"
LLM_TEMPERATURE = 0.2
LLM_MAX_TOKENS = 4096

# --- Embedding defaults ---
LLM_EMBEDDING_MODEL = "nomic-embed-text"
LLM_EMBEDDING_DIMENSIONS = 768

# --- RAG defaults ---
RAG_SIMILARITY_TOP_K = 3

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
- Import only from manim.
- Do not use external files, images, or network calls.
- Keep animations simple and clear.
- Respond ONLY with the Python code, no markdown fences."""
