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


# --- Embedding defaults ---
LLM_EMBEDDING_MODEL = "nomic-embed-text"
LLM_EMBEDDING_DIMENSIONS = 768

# --- System prompts ---
llm_prompts_dir = Path(__file__).parent.parent / "llm_knowledge" / "prompts"

PLAN_SYSTEM_PROMPT = (llm_prompts_dir / "PLAN_SYSTEM_PROMPT.md").read_text()
CODEGEN_SYSTEM_PROMPT = (llm_prompts_dir / "CODEGEN_SYSTEM_PROMPT.md").read_text()
CODEGEN_FIX_SYSTEM_PROMPT = (llm_prompts_dir / "CODEGEN_FIX_SYSTEM_PROMPT.md").read_text()

# --- RAG defaults ---
from app.llm_knowledge.skill_documents import RuleCategory  

RAG_SIMILARITY_TOP_K = 2
RAG_MAX_EMBED_CHARS = 4_000
RAG_RULE_CAP = 15
RAG_TEMPLATE_CAP = 3
RAG_EXAMPLE_CAP = 2
RULE_CATEGORY_MINS: dict[RuleCategory, int] = {
    RuleCategory.GENERAL: 1,
    RuleCategory.LAYOUT_SAFETY: 1,
    RuleCategory.VISUAL_LAYOUT: 1
}
