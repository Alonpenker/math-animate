import time

from langchain_core.messages import HumanMessage

from app.configs.llm_settings import LLM_CODEGEN_OUTPUT_MAX_TOKENS, OPENROUTER_MODELS
from app.dependencies.db import get_worker_cursor
from app.llm_knowledge.skill_documents import CORE_DOCUMENTS, REGISTRY_BY_ID
from app.schemas.knowledge import KnowledgeDocumentSeed
from app.services.nodes._context import CodegenContext
from app.services.openrouter_service import CallType, OpenRouterService
from app.services.skill_retrieval_service import SkillRetrievalService
from app.utils.logging import Logger, WorkerLog

from pydantic import BaseModel

logger = Logger.get_logger("worker")

_NODE_NAME = "document_selection"


class _SelectedSkillDocuments(BaseModel):
    selected_titles: list[str]


def make_document_selection_node(ctx: CodegenContext):
    def node(state) -> dict:
        ctx.log_node_started(_NODE_NAME)
        plan_text = state["plan"].to_prompt_text()
        user_request_text = str(state["user_request"])
        embed_text = f"{user_request_text}\n\n{plan_text}"

        with get_worker_cursor() as cursor:
            candidates = SkillRetrievalService.retrieve(cursor, embed_text)

        core_ids = {doc.document_id for doc in CORE_DOCUMENTS}
        candidate_documents: list[KnowledgeDocumentSeed] = [
            REGISTRY_BY_ID[doc.document_id]
            for doc in candidates.all_candidates
            if doc.document_id in REGISTRY_BY_ID and doc.document_id not in core_ids
        ]
        ctx.candidates_by_title = {doc.title: doc for doc in candidate_documents}

        candidate_metadata = (
            "\n".join(doc.to_metadata() for doc in candidate_documents)
            if candidate_documents
            else "(No candidate skill documents retrieved.)"
        )
        selection_prompt = (
            "From this list, select the skill documents needed to generate "
            "reliable Manim code for the lesson plan. Return only the titles "
            "that are directly relevant.\n\n"
            f"Lesson plan JSON:\n{plan_text}\n\n"
            f"Teacher request:\n{user_request_text}\n\n"
            f"Candidate documents:\n{candidate_metadata}\n\n"
            "Return exact titles from the list. Select an empty list if none are useful."
        )

        started_at = time.perf_counter()
        parsed, usage = OpenRouterService.invoke_structured(
            job_id=ctx.job_id,
            stage=ctx.current_status,
            call_type=CallType.DOCUMENT_SELECTION,
            model=OPENROUTER_MODELS.PLAN_MODEL,
            messages=[HumanMessage(content=selection_prompt)],
            schema=_SelectedSkillDocuments,
            max_tokens=LLM_CODEGEN_OUTPUT_MAX_TOKENS,
        )
        ctx.log_openrouter_call(
            CallType.DOCUMENT_SELECTION,
            started_at,
            usage,
            {
                "candidate_count": len(candidate_documents),
                "selected_count": len(parsed.selected_titles),
                "candidate_titles": [doc.title for doc in candidate_documents],
            },
            model=OPENROUTER_MODELS.PLAN_MODEL,
        )
        ctx.selected_titles = list(dict.fromkeys(parsed.selected_titles))
        logger.info(WorkerLog(
            operation="generate_code",
            event="Document selection completed",
            job_id=str(ctx.job_id),
            context={
                "candidate_count": len(candidate_documents),
                "selected_count": len(ctx.selected_titles),
                "selected_titles": ctx.selected_titles,
            },
        ))
        return {}

    return node
