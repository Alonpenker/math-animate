from pathlib import Path
from enum import StrEnum

# --- Provider & model defaults ---
class LLM_PROVIDER(StrEnum):
    OPENAI = "openai"
    OPENROUTER = "openrouter"


LLM_PLAN_MODEL = "gpt-5.2"
LLM_CODE_MODEL = "gpt-5.1-codex"
LLM_TEMPERATURE = 0.1
LLM_PLAN_OUTPUT_MAX_TOKENS = 12_000
LLM_CODEGEN_OUTPUT_MAX_TOKENS = 42_000

class OPENROUTER_MODELS(StrEnum):
    PLAN_MODEL = "openrouter/owl-alpha"
    CODING_MODEL = "poolside/laguna-m.1:free"

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_DAILY_CALL_LIMIT = 50

class LLM_REASONING_EFFORT(StrEnum):
    NONE = "none"
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"

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
RAG_RULE_CAP = 8
RAG_TEMPLATE_CAP = 3
RAG_EXAMPLE_CAP = 2
MAX_TOOL_LOADS = 8
MAX_TOOL_CALL_ITERATIONS = 10

# --- System prompts ---
llm_prompts_dir = Path(__file__).parent.parent / "llm_knowledge" / "prompts"

PLAN_SYSTEM_PROMPT = (llm_prompts_dir / "PLAN_SYSTEM_PROMPT.md").read_text()
CODEGEN_SYSTEM_PROMPT = (llm_prompts_dir / "CODEGEN_SYSTEM_PROMPT.md").read_text()
CODEGEN_FIX_SYSTEM_PROMPT = (llm_prompts_dir / "CODEGEN_FIX_SYSTEM_PROMPT.md").read_text()
