import time
from enum import StrEnum

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.configs.app_settings import settings
from app.configs.llm_settings import (
    LLM_PLAN_MODEL, LLM_CODE_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS,
    LLM_REASONING_EFFORT,
    PLAN_SYSTEM_PROMPT, CODEGEN_SYSTEM_PROMPT, CODEGEN_FIX_SYSTEM_PROMPT, RAG_SIMILARITY_TOP_K,
)
from app.dependencies.db import get_worker_cursor
from app.repositories.knowledge_repository import KnowledgeRepository
from app.schemas.knowledge import KnowledgeType
from app.schemas.user_request import UserRequest
from app.schemas.video_plan import VideoPlan
from app.services.rag_service import RAGService
from app.utils.llm_stubs import IS_E2E_MODE, STUB_PLAN, STUB_BROKEN_CODE, STUB_FIXED_CODE
from app.utils.logging import get_logger

logger = get_logger(__name__)

class CallType(StrEnum):
    PLAN = "plan"
    CODEGEN = "codegen"
    FIX = "fix"

class LLMService:

    _chat_models: dict[str, ChatOpenAI] = {}

    @classmethod
    def get_chat_model(cls, model_name: str) -> ChatOpenAI:
        if model_name not in cls._chat_models:
            cls._chat_models[model_name] = ChatOpenAI(
                model=model_name,
                temperature=LLM_TEMPERATURE,
                max_completion_tokens=LLM_MAX_TOKENS,
                reasoning_effort=LLM_REASONING_EFFORT,
                api_key=settings.openai_api_key,
            )
        return cls._chat_models[model_name]

    @classmethod
    def retrieve_examples(cls, cursor, query: str, doc_type: KnowledgeType) -> str:
        embedding = RAGService.embed_text(query)
        docs = KnowledgeRepository.search_similar(
            cursor, embedding, doc_type.value, limit=RAG_SIMILARITY_TOP_K
        )
        if not docs:
            logger.info("RAG retrieval: doc_type=%s count=0", doc_type.value)
            logger.warning(
                "No knowledge examples were retrieved for doc_type=%s. "
                "This is unexpected in a seeded environment. "
                "Load the bundled examples by calling POST /api/v1/knowledge/seed.",
                doc_type.value,
            )
            return "(No examples available.)"
        titles = [doc.title for doc in docs]
        logger.info("RAG retrieval: doc_type=%s count=%d titles=%s", doc_type.value, len(titles), titles)
        parts = []
        for i, doc in enumerate(docs, 1):
            parts.append(f"--- Example {i} ---\n{doc.content}")
        return "\n\n".join(parts)

    @staticmethod
    def _extract_token_usage(response) -> tuple[int, int, int]:
        """Return (input_tokens, output_tokens, total_tokens) from a LangChain response."""
        usage = getattr(response, "usage_metadata", None) or {}
        input_tokens = int(usage.get("input_tokens", 0))
        output_tokens = int(usage.get("output_tokens", 0))
        total_tokens = int(usage.get("total_tokens", 0))
        return input_tokens, output_tokens, total_tokens

    @staticmethod
    def _check_max_tokens(call_name: CallType, output_tokens: int) -> None:
        """Warn and raise if output tokens hit the configured max, indicating truncated output."""
        if output_tokens >= LLM_MAX_TOKENS:
            logger.warning(
                "LLM call: call=%s output_tokens=%d reached LLM_MAX_TOKENS=%d — output is likely truncated.",
                call_name, output_tokens, LLM_MAX_TOKENS,
            )
            raise ValueError(
                f"LLM call '{call_name}' hit the max token limit ({LLM_MAX_TOKENS}). "
                "Output is likely truncated and unusable."
            )

    @staticmethod
    def extract_text_content(response) -> str:
        """Extract plain text from a response whose content may be a str or a list of typed blocks."""
        content = response.content
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = [
                block["text"]
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            if text_parts:
                return "".join(text_parts)
        raise ValueError(
            f"LLM returned non-text response content. "
            f"type={type(content).__name__!r}, value={content!r}"
        )

    @staticmethod
    def render_plan_prompt(user_request: UserRequest) -> tuple[str, str]:
        """Return (system_prompt, user_query) for the planning LLM call."""
        query = (
            f"Topic: {user_request.topic}\n"
            f"Misconceptions: {', '.join(user_request.misconceptions)}\n"
            f"Constraints: {', '.join(user_request.constraints)}\n"
            f"Number of scenes: {user_request.number_of_scenes}"
        )
        with get_worker_cursor() as cursor:
            examples = LLMService.retrieve_examples(cursor, query, KnowledgeType.PLAN)
        system_prompt = PLAN_SYSTEM_PROMPT.format(examples=examples)
        return system_prompt, query

    @staticmethod
    def render_codegen_prompt(plan: VideoPlan) -> tuple[str, str]:
        """Return (system_prompt, user_query) for the codegen LLM call."""
        plan_text = plan.model_dump_json(indent=2)
        with get_worker_cursor() as cursor:
            examples = LLMService.retrieve_examples(cursor, plan_text, KnowledgeType.CODE)
        user_query = (
            f"Reference examples of good Manim code:\n{examples}\n\n"
            f"Generate Manim code for this plan:\n{plan_text}"
        )
        return CODEGEN_SYSTEM_PROMPT, user_query

    @staticmethod
    def plan_call(system_prompt: str, user_query: str) -> tuple[VideoPlan, int]:
        if IS_E2E_MODE:
            t0 = time.perf_counter()
            duration_ms = int((time.perf_counter() - t0) * 1000)
            logger.info(
                "LLM call: call=%s [E2E MODE] model=%s input_tokens=%d output_tokens=%d total_tokens=%d duration_ms=%d",
            CallType.PLAN, LLM_PLAN_MODEL, 0, 0, 0, duration_ms,
            )
            return STUB_PLAN, 0

        model = LLMService.get_chat_model(LLM_PLAN_MODEL)
        structured_model = model.with_structured_output(VideoPlan, include_raw=True)
        t0 = time.perf_counter()
        result = structured_model.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query),
        ])
        duration_ms = int((time.perf_counter() - t0) * 1000)
        if not isinstance(result, dict):
            raise ValueError("Unexpected structured output shape.")
        plan = result.get("parsed")
        input_tok, output_tok, total_tok = LLMService._extract_token_usage(result.get("raw"))
        LLMService._check_max_tokens(CallType.PLAN, output_tok)
        logger.info(
            "LLM call: call=%s model=%s input_tokens=%d output_tokens=%d total_tokens=%d duration_ms=%d",
            CallType.PLAN, LLM_PLAN_MODEL, input_tok, output_tok, total_tok, duration_ms,
        )
        if isinstance(plan, VideoPlan):
            return plan, total_tok
        raise ValueError("LLM output validation failed: response is not a valid VideoPlan instance.")

    @staticmethod
    def codegen_call(system_prompt: str, user_query: str) -> tuple[str, int]:
        if IS_E2E_MODE:
            t0 = time.perf_counter()
            duration_ms = int((time.perf_counter() - t0) * 1000)
            logger.info(
                "LLM call: call=%s [E2E MODE] model=%s input_tokens=%d output_tokens=%d total_tokens=%d duration_ms=%d",
            CallType.CODEGEN, LLM_CODE_MODEL, 0, 0, 0, duration_ms,
            )
            return STUB_BROKEN_CODE, 0

        model = LLMService.get_chat_model(LLM_CODE_MODEL)
        t0 = time.perf_counter()
        response = model.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query),
        ])
        duration_ms = int((time.perf_counter() - t0) * 1000)
        input_tok, output_tok, total_tok = LLMService._extract_token_usage(response)
        LLMService._check_max_tokens(CallType.CODEGEN, output_tok)
        logger.info(
            "LLM call: call=%s model=%s input_tokens=%d output_tokens=%d total_tokens=%d duration_ms=%d",
            CallType.CODEGEN, LLM_CODE_MODEL, input_tok, output_tok, total_tok, duration_ms,
        )
        return LLMService.extract_text_content(response), total_tok

    @staticmethod
    def render_fix_prompt(code: str, error_context: str) -> tuple[str, str]:
        user_query = (
            f"Fix this Manim code:\n\n"
            f"<code>\n{code}\n</code>\n\n"
            f"It failed with this error:\n"
            f"<error>\n{error_context}\n</error>\n\n"
            f"Return only the corrected Python code."
        )
        return CODEGEN_FIX_SYSTEM_PROMPT, user_query

    @staticmethod
    def fix_call(system_prompt: str, user_query: str) -> tuple[str, int]:
        if IS_E2E_MODE:
            t0 = time.perf_counter()
            duration_ms = int((time.perf_counter() - t0) * 1000)
            logger.info(
                "LLM call: call=%s [E2E MODE] model=%s input_tokens=%d output_tokens=%d total_tokens=%d duration_ms=%d",
            CallType.FIX, LLM_CODE_MODEL, 0, 0, 0, duration_ms,
            )
            return STUB_FIXED_CODE, 0

        model = LLMService.get_chat_model(LLM_CODE_MODEL)
        t0 = time.perf_counter()
        response = model.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query),
        ])
        duration_ms = int((time.perf_counter() - t0) * 1000)
        input_tok, output_tok, total_tok = LLMService._extract_token_usage(response)
        LLMService._check_max_tokens(CallType.FIX, output_tok)
        logger.info(
            "LLM call: call=%s model=%s input_tokens=%d output_tokens=%d total_tokens=%d duration_ms=%d",
            CallType.FIX, LLM_CODE_MODEL, input_tok, output_tok, total_tok, duration_ms,
        )
        return LLMService.extract_text_content(response), total_tok
