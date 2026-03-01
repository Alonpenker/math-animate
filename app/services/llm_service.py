from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from app.configs.app_settings import settings
from app.configs.llm_settings import (
    LLMProvider, LLM_PROVIDER, LLM_PLAN_MODEL, LLM_CODE_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS,
    LLM_REASONING_EFFORT,
    PLAN_SYSTEM_PROMPT, CODEGEN_SYSTEM_PROMPT, CODEGEN_FIX_SYSTEM_PROMPT, RAG_SIMILARITY_TOP_K,
)
from app.dependencies.db import get_worker_cursor
from app.repositories.knowledge_repository import KnowledgeRepository
from app.schemas.knowledge import KnowledgeType
from app.schemas.user_request import UserRequest
from app.schemas.video_plan import VideoPlan
from app.services.rag_service import RAGService


class LLMService:

    PROVIDERS = {
        LLMProvider.OPENAI: lambda model_name: ChatOpenAI(
            model=model_name,
            temperature=LLM_TEMPERATURE,
            max_completion_tokens=LLM_MAX_TOKENS,
            reasoning_effort=LLM_REASONING_EFFORT,
            api_key=settings.api_key,
        ),
        LLMProvider.ANTHROPIC: lambda model_name: ChatAnthropic(
            model_name=model_name,
            temperature=LLM_TEMPERATURE,
            max_tokens_to_sample=LLM_MAX_TOKENS,
            api_key=settings.api_key,
            timeout=None,
            stop=None
        ),
    }

    _chat_models: dict[str, ChatOpenAI | ChatAnthropic] = {}

    @classmethod
    def get_chat_model(cls, model_name: str) -> ChatOpenAI | ChatAnthropic:
        if model_name not in cls._chat_models:
            builder = cls.PROVIDERS.get(LLM_PROVIDER)
            if builder is None:
                raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")
            cls._chat_models[model_name] = builder(model_name)
        return cls._chat_models[model_name]

    @classmethod
    def retrieve_examples(cls, cursor, query: str, doc_type: KnowledgeType) -> str:
        embedding = RAGService.embed_text(query)
        docs = KnowledgeRepository.search_similar(
            cursor, embedding, doc_type.value, limit=RAG_SIMILARITY_TOP_K
        )
        if not docs:
            return "(No examples available.)"
        parts = []
        for i, doc in enumerate(docs, 1):
            parts.append(f"--- Example {i} ---\n{doc.content}")
        return "\n\n".join(parts)

    @staticmethod
    def extract_total_tokens(response) -> int:
        usage = getattr(response, "usage_metadata", None) or {}
        return int(usage.get("total_tokens", 0))

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
        model = LLMService.get_chat_model(LLM_PLAN_MODEL)
        structured_model = model.with_structured_output(VideoPlan, include_raw=True)
        result = structured_model.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query),
        ])
        if not isinstance(result, dict):
            raise ValueError("Unexpected structured output shape.")
        plan = result.get("parsed")
        total_tokens = LLMService.extract_total_tokens(result.get("raw"))
        if isinstance(plan, VideoPlan):
            return plan, total_tokens
        raise ValueError("LLM output validation failed: response is not a valid VideoPlan instance.")

    @staticmethod
    def codegen_call(system_prompt: str, user_query: str) -> tuple[str, int]:
        model = LLMService.get_chat_model(LLM_CODE_MODEL)
        response = model.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query),
        ])
        total_tokens = LLMService.extract_total_tokens(response)
        return LLMService.extract_text_content(response), total_tokens

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
        model = LLMService.get_chat_model(LLM_CODE_MODEL)
        response = model.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_query),
        ])
        total_tokens = LLMService.extract_total_tokens(response)
        return LLMService.extract_text_content(response), total_tokens
