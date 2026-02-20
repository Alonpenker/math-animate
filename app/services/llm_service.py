from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from app.configs.app_settings import settings
from app.configs.llm_settings import (
    LLMProvider, LLM_PROVIDER, LLM_PLAN_MODEL, LLM_CODE_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS,
    PLAN_SYSTEM_PROMPT, CODEGEN_SYSTEM_PROMPT, RAG_SIMILARITY_TOP_K,
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

    _chat_models = {}

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
    def plan_call(user_request: UserRequest) -> VideoPlan:
        query = (
            f"Topic: {user_request.topic}\n"
            f"Misconceptions: {', '.join(user_request.misconceptions)}\n"
            f"Constraints: {', '.join(user_request.constraints)}\n"
            f"Number of scenes: {user_request.number_of_scenes}"
        )

        with get_worker_cursor() as cursor:
            examples = LLMService.retrieve_examples(cursor, query, KnowledgeType.PLAN)

        system_prompt = PLAN_SYSTEM_PROMPT.format(examples=examples)
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{query}"),
        ])

        model = LLMService.get_chat_model(LLM_PLAN_MODEL)
        structured_model = model.with_structured_output(VideoPlan)
        chain = prompt | structured_model
        plan = chain.invoke({"query": query})
        if isinstance(plan, VideoPlan):
            return plan
        raise ValueError("LLM output validation failed: response is not a valid VideoPlan instance.")
        

    @staticmethod
    def codegen_call(plan: VideoPlan) -> str:
        plan_text = plan.model_dump_json(indent=2)

        with get_worker_cursor() as cursor:
            examples = LLMService.retrieve_examples(cursor, plan_text, KnowledgeType.CODE)

        system_prompt = CODEGEN_SYSTEM_PROMPT.format(examples=examples)
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Generate Manim code for this plan:\n{plan}"),
        ])

        model = LLMService.get_chat_model(LLM_CODE_MODEL)
        chain = prompt | model
        response = chain.invoke({"plan": plan_text})
        content = response.content
        if isinstance(content, str):
            return content
        raise ValueError("LLM returned non-text response content for code generation.")
