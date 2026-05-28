import time
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage

from lab_logging import LabLog
from llm_client import invoke_structured
from runtime.context import ExperimentContext
from schemas import VideoPlan
from settings import (
    OPENROUTER_PLAN_MODEL,
    PLAN_OUTPUT_MAX_TOKENS,
    ArchivedPromptFiles,
    PromptFiles,
    UsageFileNames,
)
from workflow_state import NodeName, WorkflowState


def make_generate_plan_node(ctx: ExperimentContext, name: NodeName):
    operation = name.value

    def node(state: WorkflowState) -> dict:
        request_text = state["request_text"]
        ctx.run_logger.info(LabLog(operation=operation, event="Node started"))
        ctx.files.archive_prompt_file(
            PromptFiles.PLAN_SYSTEM,
            ArchivedPromptFiles.GENERATE_PLAN_SYSTEM,
        )
        ctx.files.write_prompt(ArchivedPromptFiles.GENERATE_PLAN_USER, request_text)

        if ctx.provided_plan_path:
            raw_plan_text = Path(ctx.provided_plan_path).read_text(encoding="utf-8")
            plan = VideoPlan.model_validate_json(raw_plan_text)
            ctx.files.save_plan(plan)
            ctx.run_logger.info(LabLog(
                operation=operation,
                event="Plan loaded from file",
                context={
                    "plan_path": str(ctx.provided_plan_path),
                    "scene_count": len(plan.scenes),
                    "plan_chars": len(plan.to_prompt_text()),
                },
            ))
            return {"plan": plan}

        system_prompt = ctx.files.read_prompt(PromptFiles.PLAN_SYSTEM)
        ctx.run_logger.info(LabLog(
            operation=operation,
            event="OpenRouter call started",
            context={
                "model": OPENROUTER_PLAN_MODEL,
                "max_tokens": PLAN_OUTPUT_MAX_TOKENS,
            },
        ))
        started_at = time.perf_counter()
        plan, usage = invoke_structured(
            model=OPENROUTER_PLAN_MODEL,
            messages=[
                SystemMessage(content=system_prompt),
                HumanMessage(content=request_text),
            ],
            schema=VideoPlan,
            max_tokens=PLAN_OUTPUT_MAX_TOKENS,
        )
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        plan_prompt_text = plan.to_prompt_text()
        ctx.files.save_plan(plan)
        cumulative_usage = ctx.usage.record(
            UsageFileNames.GENERATE_PLAN,
            usage,
            duration_ms,
        )
        ctx.usage.log_llm_completed(
            ctx.run_logger,
            operation=operation,
            model=OPENROUTER_PLAN_MODEL,
            duration_ms=duration_ms,
            usage=usage,
            cumulative_usage=cumulative_usage,
            extra_context={
                "scene_count": len(plan.scenes),
                "plan_chars": len(plan_prompt_text),
            },
        )
        return {"plan": plan}

    return node
