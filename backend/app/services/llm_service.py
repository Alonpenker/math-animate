import time
from enum import StrEnum

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from openai import LengthFinishReasonError

from app.configs.app_settings import settings
from app.configs.llm_settings import (
    LLM_PLAN_MODEL, LLM_CODE_MODEL, LLM_TEMPERATURE,
    LLM_PLAN_OUTPUT_MAX_TOKENS, LLM_CODEGEN_OUTPUT_MAX_TOKENS,
    LLM_REASONING_EFFORT,
    PLAN_SYSTEM_PROMPT, CODEGEN_SYSTEM_PROMPT, CODEGEN_FIX_SYSTEM_PROMPT, RAG_SIMILARITY_TOP_K,
)
from app.dependencies.db import get_worker_cursor
from app.exceptions.llm_usage_exception import LLMUsageException
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

    _plan_model: ChatOpenAI | None = None
    _codegen_model: ChatOpenAI | None = None

    @classmethod
    def _get_plan_model(cls) -> ChatOpenAI:
        if cls._plan_model is None:
            cls._plan_model = ChatOpenAI(
                model=LLM_PLAN_MODEL,
                temperature=LLM_TEMPERATURE,
                max_completion_tokens=LLM_PLAN_OUTPUT_MAX_TOKENS,
                reasoning_effort=LLM_REASONING_EFFORT,
                api_key=settings.openai_api_key,
            )
        return cls._plan_model

    @classmethod
    def _get_codegen_model(cls) -> ChatOpenAI:
        if cls._codegen_model is None:
            cls._codegen_model = ChatOpenAI(
                model=LLM_CODE_MODEL,
                temperature=LLM_TEMPERATURE,
                max_completion_tokens=LLM_CODEGEN_OUTPUT_MAX_TOKENS,
                reasoning_effort=LLM_REASONING_EFFORT,
                api_key=settings.openai_api_key,
            )
        return cls._codegen_model

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
    def _extract_token_usage(response) -> tuple[int, int, int, int]:
        """Return (input_tokens, output_tokens, total_tokens, reasoning_tokens) from a LangChain response."""
        usage_metadata = getattr(response, "usage_metadata", None) # For raw_response
        if usage_metadata is not None:
            input_tokens = int(usage_metadata.get("input_tokens", 0))
            output_tokens = int(usage_metadata.get("output_tokens", 0))
            total_tokens = int(usage_metadata.get("total_tokens", 0))
            output_details = usage_metadata.get("output_token_details", {})
            reasoning_tokens = int(output_details.get("reasoning", 0))
            return input_tokens, output_tokens, total_tokens, reasoning_tokens

        usage = getattr(response, "usage", None) # For exc.completion
        if usage is not None:
            input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
            output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
            total_tokens = int(getattr(usage, "total_tokens", 0) or 0)
            completion_details = getattr(usage, "completion_tokens_details", None)
            reasoning_tokens = int(getattr(completion_details, "reasoning_tokens", 0) or 0)
            return input_tokens, output_tokens, total_tokens, reasoning_tokens

        raise RuntimeError(
            "Could not extract token usage from LLM response. "
            f"response_type={type(response).__name__}"
        )

    @staticmethod
    def _check_max_tokens(
        call_name: CallType,
        *,
        input_tokens: int,
        reasoning_tokens: int,
        output_tokens: int,
        total_tokens: int,
        max_tokens: int,
    ) -> None:
        """Warn and raise if output tokens hit the configured max, indicating truncated output."""
        if output_tokens >= max_tokens:
            logger.warning(
                "LLM call failed: call=%s input_tokens=%d reasoning_tokens=%d output_tokens=%d total_tokens=%d max_tokens=%d reason=max_tokens_reached",
                call_name, input_tokens, reasoning_tokens, output_tokens, total_tokens, max_tokens,
            )
            raise LLMUsageException(
                f"LLM call '{call_name}' hit the max token limit ({max_tokens}). "
                "Output is likely truncated and unusable.",
                total_tokens=total_tokens,
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
        request_text = (
            f"Topic: {user_request.topic}\n"
            f"Misconceptions: {', '.join(user_request.misconceptions)}\n"
            f"Constraints: {', '.join(user_request.constraints)}\n"
            f"Number of scenes: {user_request.number_of_scenes}"
        )
        with get_worker_cursor() as cursor:
            examples = LLMService.retrieve_examples(cursor, request_text, KnowledgeType.PLAN)
        user_query = (
            f"Reference examples of good plans:\n{examples}\n\n"
            f"Generate a scene plan for this request:\n{request_text}"
        )
        return PLAN_SYSTEM_PROMPT, user_query

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
                "LLM call finished [E2E MODE]: call=%s model=%s input_tokens=%d reasoning_tokens=%d output_tokens=%d total_tokens=%d duration_ms=%d",
                CallType.PLAN, LLM_PLAN_MODEL, 0, 0, 0, 0, duration_ms,
            )
            return STUB_PLAN, 0

        model = LLMService._get_plan_model()
        structured_model = model.with_structured_output(VideoPlan, include_raw=True)
        t0 = time.perf_counter()
        try:
            result = structured_model.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query),
            ])
        except LengthFinishReasonError as exc:
            duration_ms = int((time.perf_counter() - t0) * 1000)
            input_tok, output_tok, total_tok, reasoning_tok = LLMService._extract_token_usage(exc.completion)
            logger.warning(
                "LLM call failed: call=%s model=%s input_tokens=%d reasoning_tokens=%d output_tokens=%d total_tokens=%d duration_ms=%d reason=length_finish_reason",
                CallType.PLAN, LLM_PLAN_MODEL, input_tok, reasoning_tok, output_tok, total_tok, duration_ms,
            )
            raise LLMUsageException(
                f"LLM call '{CallType.PLAN}' exhausted its output token budget "
                f"({LLM_PLAN_OUTPUT_MAX_TOKENS}) before producing a usable plan.",
                total_tokens=total_tok,
            ) from exc
        except Exception as exc:
            duration_ms = int((time.perf_counter() - t0) * 1000)
            logger.warning(
                "LLM call failed: call=%s model=%s duration_ms=%d reason=%s",
                CallType.PLAN, LLM_PLAN_MODEL, duration_ms, type(exc).__name__,
            )
            raise RuntimeError(
                f"LLM call '{CallType.PLAN}' failed before producing a usable plan: {type(exc).__name__}",
            ) from exc
        duration_ms = int((time.perf_counter() - t0) * 1000)
        raw_response = result.get("raw") if isinstance(result, dict) else None
        input_tok, output_tok, total_tok, reasoning_tok = LLMService._extract_token_usage(raw_response)
        LLMService._check_max_tokens(
            CallType.PLAN,
            input_tokens=input_tok,
            reasoning_tokens=reasoning_tok,
            output_tokens=output_tok,
            total_tokens=total_tok,
            max_tokens=LLM_PLAN_OUTPUT_MAX_TOKENS,
        )
        logger.info(
            "LLM call finished: call=%s model=%s input_tokens=%d reasoning_tokens=%d output_tokens=%d total_tokens=%d duration_ms=%d",
            CallType.PLAN, LLM_PLAN_MODEL, input_tok, reasoning_tok, output_tok, total_tok, duration_ms,
        )
        if not isinstance(result, dict):
            logger.warning(
                "LLM output validation failed: structured response has an unexpected shape (response_type=%s, expected dict).",
                type(result).__name__,
            )
            raise LLMUsageException(
                f"LLM output validation failed: structured response has an unexpected shape (response_type={type(result).__name__}, expected dict).",
                total_tokens=total_tok,
            )
        
        plan = result.get("parsed")
        if isinstance(plan, VideoPlan):
            for scene in plan.scenes:
                if scene.scene_number == -1:
                    logger.warning("LLM output validation failed: non-math topic detected (%s).",
                                    scene.learning_objective,
                                    )
                    raise LLMUsageException(
                        f"LLM output validation failed: non-math topic detected ({scene.learning_objective})",
                        total_tokens=total_tok,
                    )
            return plan, total_tok
        
        logger.warning(
            "LLM output validation failed: response is not a valid instance (parsed_type=%s, expected VideoPlan).",
            type(plan).__name__,
        )
        raise LLMUsageException(
            f"LLM output validation failed: response is not a valid instance (parsed_type={type(plan).__name__}, expected VideoPlan).",
            total_tokens=total_tok,
        )

    @staticmethod
    def codegen_call(system_prompt: str, user_query: str) -> tuple[str, int]:
        if IS_E2E_MODE:
            t0 = time.perf_counter()
            duration_ms = int((time.perf_counter() - t0) * 1000)
            logger.info(
                "LLM call finished [E2E MODE]: call=%s model=%s input_tokens=%d reasoning_tokens=%d output_tokens=%d total_tokens=%d duration_ms=%d",
                CallType.CODEGEN, LLM_CODE_MODEL, 0, 0, 0, 0, duration_ms,
            )
            return STUB_BROKEN_CODE, 0

        model = LLMService._get_codegen_model()
        t0 = time.perf_counter()
        try:
            response = model.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query),
            ])
        except LengthFinishReasonError as exc:
            duration_ms = int((time.perf_counter() - t0) * 1000)
            input_tok, output_tok, total_tok, reasoning_tok = LLMService._extract_token_usage(exc.completion)
            logger.warning(
                "LLM call failed: call=%s model=%s input_tokens=%d reasoning_tokens=%d output_tokens=%d total_tokens=%d duration_ms=%d reason=length_finish",
                CallType.CODEGEN, LLM_CODE_MODEL, input_tok, reasoning_tok, output_tok, total_tok, duration_ms,
            )
            raise LLMUsageException(
                f"LLM call '{CallType.CODEGEN}' hit the token limit ({LLM_CODEGEN_OUTPUT_MAX_TOKENS}) before finishing output.",
                total_tokens=total_tok,
            ) from exc
        except Exception as exc:
            duration_ms = int((time.perf_counter() - t0) * 1000)
            logger.warning(
                "LLM call failed: call=%s model=%s duration_ms=%d reason=%s",
                CallType.CODEGEN, LLM_CODE_MODEL, duration_ms, type(exc).__name__,
            )
            raise RuntimeError(
                f"LLM call '{CallType.CODEGEN}' failed before producing code: {type(exc).__name__}",
            ) from exc
        duration_ms = int((time.perf_counter() - t0) * 1000)
        input_tok, output_tok, total_tok, reasoning_tok = LLMService._extract_token_usage(response)
        LLMService._check_max_tokens(
            CallType.CODEGEN,
            input_tokens=input_tok,
            reasoning_tokens=reasoning_tok,
            output_tokens=output_tok,
            total_tokens=total_tok,
            max_tokens=LLM_CODEGEN_OUTPUT_MAX_TOKENS,
        )
        logger.info(
            "LLM call finished: call=%s model=%s input_tokens=%d reasoning_tokens=%d output_tokens=%d total_tokens=%d duration_ms=%d",
            CallType.CODEGEN, LLM_CODE_MODEL, input_tok, reasoning_tok, output_tok, total_tok, duration_ms,
        )
        try:
            return LLMService.extract_text_content(response), total_tok
        except ValueError as exc:
            logger.warning(
                "LLM output validation failed: codegen response did not contain plain text content.",
            )
            raise LLMUsageException(
                "LLM output validation failed: codegen response did not contain plain text content.",
                total_tokens=total_tok,
            ) from exc

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
                "LLM call finished [E2E MODE]: call=%s model=%s input_tokens=%d reasoning_tokens=%d output_tokens=%d total_tokens=%d duration_ms=%d",
                CallType.FIX, LLM_CODE_MODEL, 0, 0, 0, 0, duration_ms,
            )
            return STUB_FIXED_CODE, 0

        model = LLMService._get_codegen_model()
        t0 = time.perf_counter()
        try:
            response = model.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query),
            ])
        except LengthFinishReasonError as exc:
            duration_ms = int((time.perf_counter() - t0) * 1000)
            input_tok, output_tok, total_tok, reasoning_tok = LLMService._extract_token_usage(exc.completion)
            logger.warning(
                "LLM call failed: call=%s model=%s input_tokens=%d reasoning_tokens=%d output_tokens=%d total_tokens=%d duration_ms=%d reason=length_finish",
                CallType.FIX, LLM_CODE_MODEL, input_tok, reasoning_tok, output_tok, total_tok, duration_ms,
            )
            raise LLMUsageException(
                f"LLM call '{CallType.FIX}' hit the token limit ({LLM_CODEGEN_OUTPUT_MAX_TOKENS}) before finishing output.",
                total_tokens=total_tok,
            ) from exc
        except Exception as exc:
            duration_ms = int((time.perf_counter() - t0) * 1000)
            logger.warning(
                "LLM call failed: call=%s model=%s duration_ms=%d reason=%s",
                CallType.FIX, LLM_CODE_MODEL, duration_ms, type(exc).__name__,
            )
            raise RuntimeError(
                f"LLM call '{CallType.FIX}' failed before producing fixed code: {type(exc).__name__}",
            ) from exc
        duration_ms = int((time.perf_counter() - t0) * 1000)
        input_tok, output_tok, total_tok, reasoning_tok = LLMService._extract_token_usage(response)
        LLMService._check_max_tokens(
            CallType.FIX,
            input_tokens=input_tok,
            reasoning_tokens=reasoning_tok,
            output_tokens=output_tok,
            total_tokens=total_tok,
            max_tokens=LLM_CODEGEN_OUTPUT_MAX_TOKENS,
        )
        logger.info(
            "LLM call finished: call=%s model=%s input_tokens=%d reasoning_tokens=%d output_tokens=%d total_tokens=%d duration_ms=%d",
            CallType.FIX, LLM_CODE_MODEL, input_tok, reasoning_tok, output_tok, total_tok, duration_ms,
        )
        try:
            return LLMService.extract_text_content(response), total_tok
        except ValueError as exc:
            logger.warning(
                "LLM output validation failed: fix response did not contain plain text content.",
            )
            raise LLMUsageException(
                "LLM output validation failed: fix response did not contain plain text content.",
                total_tokens=total_tok,
            ) from exc
