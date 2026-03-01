from enum import Enum


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


# --- Provider & model defaults ---
LLM_PROVIDER = LLMProvider.OPENAI
LLM_PLAN_MODEL = "gpt-5.2"
LLM_CODE_MODEL = "gpt-5.1-codex"
LLM_TEMPERATURE = 0.2
LLM_MAX_TOKENS = 12_288  # TODO: revisit after REQ-5 iteration reveals typical code sizes and token usage patterns
LLM_REASONING_EFFORT = "low"

# --- Embedding defaults ---
LLM_EMBEDDING_MODEL = "nomic-embed-text"
LLM_EMBEDDING_DIMENSIONS = 768

# --- RAG defaults ---
RAG_SIMILARITY_TOP_K = 5

# --- Token budget defaults ---
DAILY_TOKEN_LIMIT = 250_000
SOFT_THRESHOLD_RATIO = 0.8
PLANNING_OUTPUT_BUFFER = 2_048
CODEGEN_OUTPUT_BUFFER = 4_096  # TODO: revisit after REQ-3/REQ-5 iteration reveals typical code sizes
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

# ALLOWED IMPORTS
- Import only from manim, numpy, math, colour, scipy, random and typing.
- Do not use external files, images, or network calls.

# STRUCTURAL RULES
- Each scene class must be named Scene1, Scene2, etc.
- Each scene class must define construct(). Helper functions may live at module scope.
- Keep animations simple, clear, and self-contained.

# FORBIDDEN PATTERNS
- Never use `always_redraw` with structurally variable mobjects -- any mobject whose submobject count depends on its geometry: `DashedLine`, `DashedVMobject`, 
    `VGroup` built dynamically. These cause `IndexError` in Manim v0.19.2 when `become()` tries to align mismatched subpath counts.
- For a dashed indicator line whose endpoints move, use a plain `Line` inside `always_redraw` instead -- its structure is always a single path.
- For any geometric mobject (Line, Arc, Polygon) that must track a moving point, use `add_updater` with positional mutations 
    (`put_start_and_end_on`, `move_to`) on a pre-constructed instance rather than recreating it each frame.
- Never call `become()` across mobjects with different submobject structures.

# VIDEO DESIGN RULES
- Keep all text, labels, and equations fully on screen, non-overlapping, and in dedicated label zones.
- Ensure important text stays on screen long enough to read, usually at least 1 second before the next transition.
- Do not use instant cuts between major visual elements; use FadeIn/FadeOut or Create with a run_time of at least 0.5s.
- When one math expression, function, or calculation step becomes another, show that change with TransformMatchingTex, TransformFromCopy, or another direct transform. Do not fade out one math object and fade in the replacement when they represent the same evolving calculation.
- For equation-solving scenes, keep the equals sign fixed and transform the left and right sides around it instead of replacing the whole equation.
- When a number, symbol, or expression is reused with the same meaning elsewhere, animate that exact value from its original location into the new 
    equation, expression, label, or final answer instead of introducing it as a fresh object. Prefer TransformMatchingTex, TransformFromCopy, or 
    moving copied submobjects over fade-in/fade-out for repeated math.
- When showing an inverse operation, copy the relevant symbol or term from the expression and animate that cue; do not invent temporary preview text.

# OUTPUT FORMAT
- Respond ONLY with the Python code, no markdown fences."""

CODEGEN_FIX_SYSTEM_PROMPT = """You are an expert Manim v0.19.2 developer fixing a specific bug in existing code.
You will receive broken Manim code and the exact error it produced.
Fix only the specific issue. Do not rewrite scenes from scratch.
Preserve all Scene class names (Scene1, Scene2, ...) and the overall structure.

Rules:
- Import only from manim, numpy, math, colour, scipy, random and typing.
- Do not use external files, images, or network calls.
- Respond ONLY with the corrected Python code, no markdown fences."""
