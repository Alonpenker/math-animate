import time

from langchain_core.messages import HumanMessage

from lab_logging import LabLog
from runtime.context import ExperimentContext
from services.code_extractor import extract_code
from settings import (
    CODEGEN_OUTPUT_MAX_TOKENS,
    OPENROUTER_CODE_MODEL,
    ArchivedPromptFiles,
    UsageFileNames,
)
from workflow_state import NodeName, WorkflowState


def make_generate_code_node(ctx: ExperimentContext, name: NodeName):
    operation = name.value

    def node(state: WorkflowState) -> dict:
        ctx.run_logger.info(LabLog(operation=operation, event="Node started"))
        plan = state["plan"]
        if plan is None:
            raise RuntimeError("Cannot generate code without a plan.")

        plan_prompt_text = plan.to_prompt_text()
        human_message = HumanMessage(
            content=f"Generate Manim code for this lesson plan:\n\n{plan_prompt_text}"
        )
        ctx.files.write_prompt(
            ArchivedPromptFiles.GENERATE_CODE_USER,
            human_message.content,
        )

        ctx.run_logger.info(LabLog(
            operation=operation,
            event="OpenRouter call started",
            context={
                "model": OPENROUTER_CODE_MODEL,
                "max_tokens": CODEGEN_OUTPUT_MAX_TOKENS,
                "reasoning_effort": "low",
                "plan_chars": len(plan_prompt_text),
            },
        ))
        started_at = time.perf_counter()
        response, usage = ctx.llm.invoke(
            model=OPENROUTER_CODE_MODEL,
            messages=[*state["messages"], human_message],
            max_tokens=CODEGEN_OUTPUT_MAX_TOKENS,
            reasoning_effort="low",
        )
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        code = extract_code(response)
        ctx.files.save_attempt_code(0, code)
        cumulative_usage = ctx.usage.record(
            UsageFileNames.GENERATE_CODE,
            usage,
            duration_ms,
        )
        ctx.usage.log_llm_completed(
            ctx.run_logger,
            operation=operation,
            model=OPENROUTER_CODE_MODEL,
            duration_ms=duration_ms,
            usage=usage,
            cumulative_usage=cumulative_usage,
            extra_context={
                "reasoning_effort": "low",
                "code_chars": len(code),
                "attempt": 0,
            },
        )
        return {"messages": [human_message, response], "code": code}

    return node
