from lab_logging import LabLog
from runtime.context import ExperimentContext
from verify_render import summarize_verification_failure
from workflow_state import NodeName, WorkflowState


def make_fail_node(ctx: ExperimentContext, name: NodeName):
    operation = name.value

    def node(state: WorkflowState) -> dict:
        verification = state["verification"]
        ctx.run_logger.error(LabLog(
            operation=operation,
            event="Workflow failed",
            context={
                "fix_attempts": state["fix_attempt"],
                "verification_fixable": verification.fixable,
                "failure_summary": summarize_verification_failure(verification.failure),
            },
        ))
        ctx.write_summary({
            "status": "failed_verification",
            "run_dir": str(ctx.files.run_dir),
            "fix_attempts": state["fix_attempt"],
            "verification_fixable": verification.fixable,
            "failure_summary": summarize_verification_failure(verification.failure),
        })
        return {}

    return node
