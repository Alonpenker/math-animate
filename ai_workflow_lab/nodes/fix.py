import time

from langchain_core.messages import HumanMessage, SystemMessage

from lab_logging import LabLog
from runtime.context import ExperimentContext
from services.code_extractor import extract_code
from settings import (
    CODEGEN_OUTPUT_MAX_TOKENS,
    MAX_FIX_ATTEMPTS,
    OPENROUTER_CODE_MODEL,
    ArchivedPromptFiles,
    PromptFiles,
    UsageFileNames,
)
from workflow_state import NodeName, WorkflowState


def make_fix_code_node(ctx: ExperimentContext, name: NodeName):
    operation = name.value

    def node(state: WorkflowState) -> dict:
        attempt = state["fix_attempt"] + 1
        verification = state["verification"]
        code_plan = state["code_plan"]
        ctx.run_logger.info(LabLog(
            operation=operation,
            event="Node started",
            context={"attempt": attempt, "max_fix_attempts": MAX_FIX_ATTEMPTS},
        ))
        ctx.files.archive_prompt_file(
            PromptFiles.CODEGEN_FIX_SYSTEM,
            ArchivedPromptFiles.FIX_SYSTEM,
        )
        fix_instruction = HumanMessage(
            content=(
                f"Attempt {attempt} of {MAX_FIX_ATTEMPTS}: verification failed.\n\n"
                f"{verification.failure}\n\n"
                "Teacher request:\n"
                f"{state['request_text']}\n\n"
                "Video plan JSON:\n"
                f"{state['plan'].to_prompt_text() if state['plan'] else '(missing plan)'}\n\n"
                "Code plan JSON:\n"
                f"{code_plan.to_prompt_text() if code_plan else '(missing code plan)'}\n\n"
                "Preserve the code plan's object lifecycle, subscene cleanup, "
                "visual block ownership, helper contracts, and layout budgets "
                "while fixing the reported failure.\n\n"
                "Current Python code to fix:\n"
                "```python\n"
                f"{state['code']}\n"
                "```\n\n"
                "Return a complete corrected Python script only."
            )
        )
        ctx.files.write_prompt(
            ArchivedPromptFiles.fix_attempt_user(attempt),
            fix_instruction.content,
        )

        fix_messages = [
            SystemMessage(
                content=ctx.files.read_prompt(PromptFiles.CODEGEN_FIX_SYSTEM).strip()
            ),
            fix_instruction,
        ]
        ctx.run_logger.info(LabLog(
            operation=operation,
            event="OpenRouter call started",
            context={
                "model": OPENROUTER_CODE_MODEL,
                "max_tokens": CODEGEN_OUTPUT_MAX_TOKENS,
                "reasoning_effort": "medium",
                "attempt": attempt,
            },
        ))
        started_at = time.perf_counter()
        response, usage = ctx.llm.invoke(
            model=OPENROUTER_CODE_MODEL,
            messages=fix_messages,
            max_tokens=CODEGEN_OUTPUT_MAX_TOKENS,
            reasoning_effort="medium",
        )
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        fixed_code = extract_code(response)
        ctx.files.save_attempt_code(attempt, fixed_code)
        cumulative_usage = ctx.usage.record(
            UsageFileNames.fix_attempt(attempt),
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
                "reasoning_effort": "medium",
                "attempt": attempt,
                "code_chars": len(fixed_code),
            },
        )
        return {
            "messages": [fix_instruction, response],
            "code": fixed_code,
            "fix_attempt": attempt,
        }

    return node
