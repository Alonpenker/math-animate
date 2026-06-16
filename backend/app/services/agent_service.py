from enum import StrEnum
from typing import Annotated, TypedDict
from uuid import UUID

from langchain_core.messages import BaseMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from app.domain.job_state import JobStatus
from app.exceptions.llm_usage_exception import LLMUsageException
from app.exceptions.quota_exceeded_error import QuotaExceededError
from app.schemas.code_plan import CodePlan
from app.schemas.jobs import JobPlanRequest
from app.schemas.knowledge import TemplateDocumentSeed
from app.schemas.user_request import UserRequest
from app.schemas.video_plan import VideoPlan
from app.services.nodes import (
    make_code_plan_node,
    make_codegen_node,
    make_document_selection_node,
    make_fail_node,
    make_fix_node,
    make_load_knowledge_node,
    make_save_render_node,
    make_verify_node,
)
from app.services.nodes._context import CodegenContext
from app.utils.logging import Logger, WorkerLog
from app.workers.worker_helpers import transition_job
from app.workers.worker_settings import MAX_FIX_ATTEMPTS

logger = Logger.get_logger("worker")


class NodesNames(StrEnum):
    DOCUMENT_SELECTION = "document_selection"
    LOAD_SELECTED_DOCUMENTS = "load_selected_documents"
    GENERATE_CODE_PLAN = "generate_code_plan"
    GENERATE_CODE = "generate_code"
    VERIFY = "verify"
    FIX_CODE = "fix_code"
    SAVE_AND_RENDER = "save_and_render"
    FAIL = "fail"

    @classmethod
    def non_loop_nodes(cls) -> tuple["NodesNames", ...]:
        return (
            cls.DOCUMENT_SELECTION,
            cls.LOAD_SELECTED_DOCUMENTS,
            cls.GENERATE_CODE_PLAN,
            cls.GENERATE_CODE,
            cls.VERIFY,
            cls.SAVE_AND_RENDER,
            cls.FAIL,
        )

    @classmethod
    def loop_nodes_per_fix_attempt(cls) -> tuple["NodesNames", ...]:
        return (
            cls.FIX_CODE,
            cls.VERIFY,
        )


class LangGraphCodegenState(TypedDict):
    job_id: UUID
    plan: VideoPlan
    user_request: UserRequest
    messages: Annotated[list[BaseMessage], add_messages]
    code: str
    code_plan: CodePlan | None
    referenced_templates: list[TemplateDocumentSeed]
    verification_failure: str
    fix_attempt: int
    verification_fixable: bool


def _route_after_verify(state: LangGraphCodegenState) -> str:
    if not state["verification_failure"]:
        return NodesNames.SAVE_AND_RENDER
    if not state["verification_fixable"]:
        return NodesNames.FAIL
    if state["fix_attempt"] >= MAX_FIX_ATTEMPTS:
        return NodesNames.FAIL
    return NodesNames.FIX_CODE


class AgentService:
    @staticmethod
    def run_codegen(job_request: JobPlanRequest) -> None:
        job_id = job_request.job.job_id
        ctx = CodegenContext(
            job_id=job_id,
            current_status=job_request.job.status,
        )

        default_failure_statuses = {
            JobStatus.CODEGEN: JobStatus.FAILED_CODEGEN,
            JobStatus.CODED: JobStatus.FAILED_VERIFICATION,
            JobStatus.VERIFYING: JobStatus.FAILED_VERIFICATION,
            JobStatus.FIXING: JobStatus.FAILED_VERIFICATION,
        }
        llm_call_failure_statuses = {
            JobStatus.CODEGEN: JobStatus.FAILED_LLM_USAGE,
            JobStatus.FIXING: JobStatus.FAILED_LLM_USAGE,
        }
        quota_failure_statuses = {
            JobStatus.CODEGEN: JobStatus.FAILED_QUOTA_EXCEEDED,
            JobStatus.FIXING: JobStatus.FAILED_QUOTA_EXCEEDED,
        }

        def mark_failed(overrides: dict[JobStatus, JobStatus] | None = None) -> None:
            to_status = (overrides or {}).get(ctx.current_status) or default_failure_statuses.get(ctx.current_status)
            if to_status is not None:
                transition_job(job_id, ctx.current_status, to_status)

        try:
            logger.info(WorkerLog(
                operation="generate_code",
                event="LangGraph task started",
                job_id=str(job_id),
            ))
            ctx.set_status(job_request.job.status, JobStatus.CODEGEN)

            graph = StateGraph(LangGraphCodegenState)
            graph.add_node(NodesNames.DOCUMENT_SELECTION, make_document_selection_node(ctx))
            graph.add_node(NodesNames.LOAD_SELECTED_DOCUMENTS, make_load_knowledge_node(ctx))
            graph.add_node(NodesNames.GENERATE_CODE_PLAN, make_code_plan_node(ctx))
            graph.add_node(NodesNames.GENERATE_CODE, make_codegen_node(ctx))
            graph.add_node(NodesNames.VERIFY, make_verify_node(ctx))
            graph.add_node(NodesNames.FIX_CODE, make_fix_node(ctx))
            graph.add_node(NodesNames.SAVE_AND_RENDER, make_save_render_node(ctx))
            graph.add_node(NodesNames.FAIL, make_fail_node(ctx))

            graph.set_entry_point(NodesNames.DOCUMENT_SELECTION)
            graph.add_edge(NodesNames.DOCUMENT_SELECTION, NodesNames.LOAD_SELECTED_DOCUMENTS)
            graph.add_edge(NodesNames.LOAD_SELECTED_DOCUMENTS, NodesNames.GENERATE_CODE_PLAN)
            graph.add_edge(NodesNames.GENERATE_CODE_PLAN, NodesNames.GENERATE_CODE)
            graph.add_edge(NodesNames.GENERATE_CODE, NodesNames.VERIFY)
            graph.add_conditional_edges(NodesNames.VERIFY, _route_after_verify)
            graph.add_edge(NodesNames.FIX_CODE, NodesNames.VERIFY)
            graph.add_edge(NodesNames.SAVE_AND_RENDER, END)
            graph.add_edge(NodesNames.FAIL, END)

            compiled = graph.compile()
            initial_state: LangGraphCodegenState = {
                "job_id": job_id,
                "plan": job_request.plan,
                "user_request": job_request.user_request,
                "messages": [],
                "code": "",
                "code_plan": None,
                "referenced_templates": [],
                "verification_failure": "",
                "fix_attempt": 0,
                "verification_fixable": True,
            }
            recursion_limit = (
                len(NodesNames.non_loop_nodes())
                + MAX_FIX_ATTEMPTS * len(NodesNames.loop_nodes_per_fix_attempt())
            )
            compiled.invoke(initial_state, config={"recursion_limit": recursion_limit})
            logger.info(WorkerLog(
                operation="generate_code",
                event="LangGraph task completed",
                job_id=str(job_id),
            ))
        except QuotaExceededError as exc:
            try:
                mark_failed(quota_failure_statuses)
            except Exception:
                logger.warning(WorkerLog(
                    operation="generate_code",
                    event="Failed to transition job after LangGraph quota exception",
                    job_id=str(job_id),
                ), exc_info=True)
            logger.error(WorkerLog(
                operation="generate_code",
                event="LangGraph quota exceeded",
                job_id=str(job_id),
                error=Logger.serialize_error(exc),
            ), exc_info=exc)
            raise
        except LLMUsageException as exc:
            try:
                mark_failed(llm_call_failure_statuses)
            except Exception:
                logger.warning(WorkerLog(
                    operation="generate_code",
                    event="Failed to transition job after LangGraph LLM usage exception",
                    job_id=str(job_id),
                ), exc_info=True)
            logger.error(WorkerLog(
                operation="generate_code",
                event="LangGraph failed due to LLM usage error",
                job_id=str(job_id),
                error=Logger.serialize_error(exc),
            ), exc_info=exc)
            raise
        except Exception as exc:
            try:
                mark_failed()
            except Exception:
                logger.warning(WorkerLog(
                    operation="generate_code",
                    event="Failed to transition job after LangGraph exception",
                    job_id=str(job_id),
                ), exc_info=True)
            logger.error(WorkerLog(
                operation="generate_code",
                event="LangGraph task failed",
                job_id=str(job_id),
                error=Logger.serialize_error(exc),
            ), exc_info=exc)
            raise
