import json
import time

from langchain_core.messages import HumanMessage, SystemMessage

from lab_logging import LabLog
from runtime.context import ExperimentContext
from schemas import CodeQaIssue, CodeQaReport
from settings import (
    CODE_QA_OUTPUT_MAX_TOKENS,
    OPENROUTER_QA_MODEL,
    ArchivedPromptFiles,
    LogFileNames,
    PromptFiles,
    UsageFileNames,
)
from workflow_state import NodeName, VerificationResult, WorkflowState


def make_code_qa_node(ctx: ExperimentContext, name: NodeName):
    operation = name.value

    def node(state: WorkflowState) -> dict:
        attempt = state["attempt"]
        plan = state["plan"]
        if plan is None:
            raise RuntimeError("Cannot run code QA without a plan.")
        code_plan = state["code_plan"]
        if code_plan is None:
            raise RuntimeError("Cannot run code QA without a code implementation plan.")
        code_plan_prompt_text = code_plan.to_prompt_text()

        ctx.run_logger.info(LabLog(
            operation=operation,
            event="Node started",
            context={"attempt": attempt},
        ))
        ctx.files.archive_prompt_file(
            PromptFiles.CODE_QA_SYSTEM,
            ArchivedPromptFiles.CODE_QA_SYSTEM,
        )

        user_prompt = _build_user_prompt(
            request_text=state["request_text"],
            plan_json=plan.to_prompt_text(),
            code_plan_json=code_plan_prompt_text,
            attempt=attempt,
            code=state["code"],
        )
        ctx.files.write_prompt(
            ArchivedPromptFiles.code_qa_attempt_user(attempt),
            user_prompt,
        )

        ctx.run_logger.info(LabLog(
            operation=operation,
            event="OpenRouter call started",
            context={
                "model": OPENROUTER_QA_MODEL,
                "max_tokens": CODE_QA_OUTPUT_MAX_TOKENS,
                "attempt": attempt,
                "code_chars": len(state["code"]),
                "code_plan_chars": len(code_plan_prompt_text),
            },
        ))
        started_at = time.perf_counter()
        report, usage = ctx.llm.invoke_structured(
            model=OPENROUTER_QA_MODEL,
            messages=[
                SystemMessage(
                    content=ctx.files.read_prompt(PromptFiles.CODE_QA_SYSTEM).strip()
                ),
                HumanMessage(content=user_prompt),
            ],
            schema=CodeQaReport,
            max_tokens=CODE_QA_OUTPUT_MAX_TOKENS,
            reasoning_effort=None,
        )
        duration_ms = int((time.perf_counter() - started_at) * 1000)

        report_data = report.model_dump(mode="json")
        ctx.files.write_log_json(LogFileNames.code_qa_attempt(attempt), report_data)
        cumulative_usage = ctx.usage.record(
            UsageFileNames.code_qa_attempt(attempt),
            usage,
            duration_ms,
        )

        blockers = [issue for issue in report.issues if issue.severity == "blocker"]
        warnings = [issue for issue in report.issues if issue.severity == "warning"]
        blocked = report.decision == "block" or bool(blockers)
        ctx.usage.log_llm_completed(
            ctx.run_logger,
            operation=operation,
            model=OPENROUTER_QA_MODEL,
            duration_ms=duration_ms,
            usage=usage,
            cumulative_usage=cumulative_usage,
            extra_context={
                "attempt": attempt,
                "decision": report.decision,
                "blocker_count": len(blockers),
                "warning_count": len(warnings),
            },
        )

        if blocked:
            blocking_issues = blockers or report.issues
            failure = _build_failure(report, blockers)
            ctx.run_logger.warning(LabLog(
                operation=operation,
                event="QA blocked code",
                context={
                    "attempt": attempt,
                    "blocker_count": len(blocking_issues),
                    "warning_count": len(warnings),
                    "categories": sorted({issue.category for issue in blocking_issues}),
                },
            ))
            return {
                "code_qa_completed": True,
                "verification": VerificationResult(failure=failure, fixable=True),
            }

        ctx.run_logger.info(LabLog(
            operation=operation,
            event="QA passed",
            context={
                "attempt": attempt,
                "warning_count": len(warnings),
            },
        ))
        return {"code_qa_completed": True, "verification": VerificationResult()}

    return node


def _build_user_prompt(
    *,
    request_text: str,
    plan_json: str,
    code_plan_json: str,
    attempt: int,
    code: str,
) -> str:
    return (
        "Review this generated Manim code after static verification and Docker "
        "dry-run have already passed. Focus only on code-visible visual defects "
        "before final render.\n"
        f"Current attempt: {attempt}\n\n"
        "Teacher request:\n"
        f"{request_text}\n\n"
        "Video plan JSON:\n"
        f"{plan_json}\n\n"
        "Code implementation plan JSON:\n"
        f"{code_plan_json}\n\n"
        "Use the code plan to check snapshot builder grouping, internal "
        "arrangement, subscene cleanup, and show/transform transitions. Do not invent "
        "requirements beyond the video plan and code plan.\n\n"
        "Line-numbered lesson-body Manim code:\n"
        f"{_line_number_code(code)}"
    )


def _line_number_code(code: str) -> str:
    return "\n".join(
        f"{line_number}: {line}"
        for line_number, line in enumerate(code.splitlines(), start=1)
    )


def _build_failure(report: CodeQaReport, blockers: list[CodeQaIssue]) -> str:
    blocking_issues = blockers or report.issues
    categories = sorted({issue.category for issue in blocking_issues})
    issue_lines = "\n".join(
        (
            f"- {issue.category} scene={issue.scene_number} "
            f"lines={issue.line_refs}: {issue.required_fix}"
        )
        for issue in blocking_issues
    )
    report_json = json.dumps(report.model_dump(mode="json"), indent=2)
    return (
        f"LLM code QA failed with {len(blocking_issues)} blocker(s).\n"
        f"Blocking categories: {', '.join(categories) if categories else 'none'}\n\n"
        "Blocking issues:\n"
        f"{issue_lines or '- QA decision was block but no issue was provided.'}\n\n"
        "Fix instructions:\n"
        f"{report.fix_instructions}\n\n"
        "Full QA report JSON:\n"
        f"{report_json}"
    )
