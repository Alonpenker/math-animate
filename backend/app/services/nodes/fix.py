import time

from langchain_core.messages import HumanMessage, SystemMessage

from app.configs.llm_settings import (
    CODEGEN_FIX_SYSTEM_PROMPT,
    LLM_CODEGEN_OUTPUT_MAX_TOKENS,
    LLM_REASONING_EFFORT,
    OPENROUTER_MODELS,
)
from app.domain.job_state import JobStatus
from app.llm_knowledge.skill_documents import LLMKNOWLEDGE_DIR
from app.services.nodes._assemble import assemble_file, extract_lesson_body
from app.services.nodes._context import CodegenContext
from app.services.nodes.codegen import _extract_code
from app.services.openrouter_service import CallType, OpenRouterService
from app.utils.logging import Logger, WorkerLog
from app.workers.worker_settings import MAX_FIX_ATTEMPTS

logger = Logger.get_logger("worker")

_NODE_NAME = "fix_code"
_VISUAL_KIT_API_PATH = LLMKNOWLEDGE_DIR / "manim_skill" / "rules" / "visual-kit-api.md"


def make_fix_node(ctx: CodegenContext):
    def node(state) -> dict:
        ctx.log_node_started(_NODE_NAME)
        ctx.set_status(JobStatus.VERIFYING, JobStatus.FIXING)
        attempt = state["fix_attempt"] + 1
        visual_kit_api = _VISUAL_KIT_API_PATH.read_text(encoding="utf-8")
        lesson_body = extract_lesson_body(state["code"])
        code_plan = state["code_plan"]
        fix_instruction = HumanMessage(
            content=(
                f"Attempt {attempt} of {MAX_FIX_ATTEMPTS}: verification failed.\n\n"
                "Failure:\n"
                f"{state['verification_failure']}\n\n"
                "Teacher request:\n"
                f"{str(state['user_request'])}\n\n"
                "Video plan JSON:\n"
                f"{state['plan'].to_prompt_text()}\n\n"
                "Code plan JSON:\n"
                f"{code_plan.to_prompt_text() if code_plan else '(missing code plan)'}\n\n"
                "Visual-kit API contract:\n"
                f"{visual_kit_api}\n\n"
                "Current lesson-body Python code to fix:\n"
                "```python\n"
                f"{lesson_body}\n"
                "```\n\n"
                "Return the complete corrected lesson body."
            )
        )
        knowledge_messages = [
            msg for msg in state["messages"] if isinstance(msg, SystemMessage)
        ]
        fix_messages = [
            SystemMessage(content=CODEGEN_FIX_SYSTEM_PROMPT.strip()),
            *knowledge_messages,
            fix_instruction,
        ]
        started_at = time.perf_counter()
        try:
            response, usage = OpenRouterService.invoke(
                job_id=ctx.job_id,
                stage=JobStatus.FIXING,
                call_type=CallType.FIX,
                model=OPENROUTER_MODELS.CODING_MODEL,
                messages=fix_messages,
                max_tokens=LLM_CODEGEN_OUTPUT_MAX_TOKENS,
                reasoning_effort=LLM_REASONING_EFFORT.MEDIUM,
            )
            ctx.log_openrouter_call(
                CallType.FIX,
                started_at,
                usage,
                {"attempt": attempt, "max_fix_attempts": MAX_FIX_ATTEMPTS},
                reasoning_effort=LLM_REASONING_EFFORT.MEDIUM,
            )
            fixed_lesson_body = _extract_code(response, usage)
            assembled = assemble_file(fixed_lesson_body, state["referenced_templates"])
        except Exception:
            ctx.set_status(JobStatus.FIXING, JobStatus.FAILED_VERIFICATION)
            raise

        return {
            "messages": [fix_instruction, response],
            "code": assembled,
            "fix_attempt": attempt,
        }

    return node
