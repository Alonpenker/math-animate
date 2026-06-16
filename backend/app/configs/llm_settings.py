from pathlib import Path
from enum import StrEnum

# --- Provider & model defaults ---
class LLM_PROVIDER(StrEnum):
    OPENAI = "openai"
    OPENROUTER = "openrouter"

LLM_PLAN_OUTPUT_MAX_TOKENS = 12_000
LLM_CODE_PLAN_OUTPUT_MAX_TOKENS = 8_000
LLM_CODEGEN_OUTPUT_MAX_TOKENS = 16_000

class OPENROUTER_MODELS(StrEnum):
    PLAN_MODEL = "openrouter/owl-alpha"
    CODING_MODEL = "openai/gpt-oss-120b:free"
    CODE_PLAN_MODEL = "openrouter/owl-alpha"
    BETTER_PLAN_MODEL = "google/gemma-4-31b-it"

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_DAILY_CALL_LIMIT = 200

class LLM_REASONING_EFFORT(StrEnum):
    NONE = "none"
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"


# --- System prompts ---
llm_prompts_dir = Path(__file__).parent.parent / "llm_knowledge" / "prompts"

PLAN_SYSTEM_PROMPT = (llm_prompts_dir / "PLAN_SYSTEM_PROMPT.md").read_text()
CODEGEN_SYSTEM_PROMPT = (llm_prompts_dir / "CODEGEN_SYSTEM_PROMPT.md").read_text()
CODEGEN_FIX_SYSTEM_PROMPT = (llm_prompts_dir / "CODEGEN_FIX_SYSTEM_PROMPT.md").read_text()
CODE_PLAN_SYSTEM_PROMPT = (llm_prompts_dir / "CODE_PLAN_SYSTEM_PROMPT.md").read_text()

# --- Embedding defaults ---

LLM_EMBEDDING_MODEL = "nomic-embed-text"
LLM_EMBEDDING_DIMENSIONS = 768

# --- RAG defaults ---

RAG_MAX_EMBED_CHARS = 4_000
RAG_RULE_CAP = 4
RAG_TEMPLATE_CAP = 4
