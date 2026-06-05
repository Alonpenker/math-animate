from lab_logging import LabLog
from runtime.context import ExperimentContext
from services.rendering import summarize_verification_failure
from workflow_state import INITIAL_ATTEMPT, NodeName, WorkflowState


def make_fail_node(ctx: ExperimentContext, name: NodeName):
    operation = name.value

    def node(state: WorkflowState) -> dict:
        verification = state["verification"]
        attempt = state["attempt"]
        fix_attempts = max(0, attempt - INITIAL_ATTEMPT)
        ctx.run_logger.error(LabLog(
            operation=operation,
            event="Workflow failed",
            context={
                "attempt": attempt,
                "fix_attempts": fix_attempts,
                "verification_fixable": verification.fixable,
                "failure_summary": summarize_verification_failure(verification.failure),
            },
        ))
        ctx.write_summary({
            "status": "failed_verification",
            "run_dir": str(ctx.files.run_dir),
            "attempts": attempt,
            "fix_attempts": fix_attempts,
            "verification_fixable": verification.fixable,
            "failure_summary": summarize_verification_failure(verification.failure),
        })
        return {}

    return node
