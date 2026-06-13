import time

from langchain_core.messages import HumanMessage

from app.configs.llm_settings import (
    LLM_CODEGEN_OUTPUT_MAX_TOKENS,
    LLM_REASONING_EFFORT,
    OPENROUTER_MODELS,
)
from app.domain.job_state import JobStatus
from app.exceptions.llm_usage_exception import LLMUsageException
from app.services.nodes._assemble import assemble_file
from app.services.nodes._context import CodegenContext
from app.services.openrouter_service import CallType, OpenRouterService
from app.utils.logging import Logger, WorkerLog

logger = Logger.get_logger("worker")

_NODE_NAME = "generate_code"


def make_codegen_node(ctx: CodegenContext):
    def node(state) -> dict:
        ctx.log_node_started(_NODE_NAME)
        plan_text = state["plan"].to_prompt_text()
        code_plan_text = state["code_plan"].to_prompt_text()
        human_message = HumanMessage(
            content=(
                "Generate Manim code from these JSON contracts.\n\n"
                "Video plan JSON:\n"
                f"{plan_text}\n\n"
                "Code implementation plan JSON:\n"
                f"{code_plan_text}"
            )
        )
        started_at = time.perf_counter()
        response, usage = OpenRouterService.invoke(
            job_id=ctx.job_id,
            stage=ctx.current_status,
            call_type=CallType.CODEGEN,
            model=OPENROUTER_MODELS.CODING_MODEL,
            messages=[*state["messages"], human_message],
            max_tokens=LLM_CODEGEN_OUTPUT_MAX_TOKENS,
            reasoning_effort=LLM_REASONING_EFFORT.LOW,
        )
        ctx.log_openrouter_call(
            CallType.CODEGEN,
            started_at,
            usage,
            reasoning_effort=LLM_REASONING_EFFORT.LOW,
        )
        lesson_body = _extract_code(response, usage)
        assembled = assemble_file(lesson_body, state["referenced_templates"])
        ctx.set_status(JobStatus.CODEGEN, JobStatus.CODED)
        logger.info(WorkerLog(
            operation="generate_code",
            event="Code generation completed",
            job_id=str(ctx.job_id),
        ))
        return {"messages": [human_message, response], "code": assembled}

    return node


def _extract_code(response, usage) -> str:
    content = response.content
    if isinstance(content, list):
        text_parts = [
            block["text"]
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        text = "".join(text_parts) if text_parts else ""
    elif isinstance(content, str):
        text = content
    else:
        raise LLMUsageException(
            "LLM output validation failed: response did not contain plain text code.",
            total_tokens=usage.total_tokens,
        )
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return stripped
