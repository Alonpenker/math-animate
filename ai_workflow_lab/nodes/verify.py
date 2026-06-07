import time

from lab_logging import LabLog
from runtime.context import ExperimentContext
from services.rendering import (
    dry_run_docker,
    summarize_verification_failure,
    verify_code_static,
)
from settings import LogFileNames
from workflow_state import NodeName, VerificationResult, WorkflowState


def make_verify_node(ctx: ExperimentContext, name: NodeName):
    operation = name.value

    def node(state: WorkflowState) -> dict:
        attempt = state["attempt"]
        code_path = ctx.files.save_attempt_code(
            attempt,
            state["code"],
            state["referenced_templates"],
        )
        ctx.run_logger.info(LabLog(
            operation=operation,
            event="Node started",
            context={"attempt": attempt, "code_path": str(code_path)},
        ))

        static_failure = verify_code_static(state["code"])
        if static_failure is not None:
            failure = f"Static verification failed:\n{static_failure}"
            ctx.files.write_log(LogFileNames.attempt_verify(attempt), failure + "\n")
            ctx.run_logger.warning(LabLog(
                operation=operation,
                event="Static verification failed",
                context={
                    "attempt": attempt,
                    "failure_summary": summarize_verification_failure(failure),
                },
            ))
            return {"verification": VerificationResult(failure=failure, fixable=True)}

        ctx.run_logger.info(LabLog(
            operation=operation,
            event="Docker dry-run started",
            context={"attempt": attempt},
        ))
        started_at = time.perf_counter()
        passed, error_output, is_fixable, stdout, stderr = dry_run_docker(
            code_path=code_path,
            media_dir=ctx.files.dry_run_media_dir(attempt),
            run_dir=ctx.files.run_dir,
        )
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        ctx.files.write_log(LogFileNames.attempt_dry_run_stdout(attempt), stdout)
        ctx.files.write_log(LogFileNames.attempt_dry_run_stderr(attempt), stderr)
        if passed:
            ctx.run_logger.info(LabLog(
                operation=operation,
                event="Verification passed",
                context={"attempt": attempt, "duration_ms": duration_ms},
            ))
            return {"verification": VerificationResult()}

        failure = (
            f"Dry-run failed:\n{error_output}"
            if is_fixable
            else f"Dry-run infrastructure error:\n{error_output}"
        )
        ctx.files.write_log(LogFileNames.attempt_verify(attempt), failure + "\n")
        ctx.run_logger.warning(LabLog(
            operation=operation,
            event="Verification failed",
            context={
                "attempt": attempt,
                "duration_ms": duration_ms,
                "is_fixable": is_fixable,
                "failure_summary": summarize_verification_failure(failure),
            },
        ))
        return {
            "verification": VerificationResult(
                failure=failure,
                fixable=is_fixable,
            )
        }

    return node
