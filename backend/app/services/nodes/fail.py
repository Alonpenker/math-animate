from app.domain.job_state import JobStatus
from app.services.nodes._context import CodegenContext
from app.utils.logging import Logger, WorkerLog
from app.workers.worker_helpers import summarize_verification_failure
from app.workers.worker_settings import MAX_FIX_ATTEMPTS

logger = Logger.get_logger("worker")

_NODE_NAME = "fail"


def make_fail_node(ctx: CodegenContext):
    def node(state) -> dict:
        ctx.log_node_started(_NODE_NAME)
        logger.error(WorkerLog(
            operation="generate_code",
            event="Verification failed; job failed",
            job_id=str(ctx.job_id),
            context={
                "fix_attempt": state["fix_attempt"],
                "max_fix_attempts": MAX_FIX_ATTEMPTS,
                "verification_fixable": state["verification_fixable"],
                "failure_summary": summarize_verification_failure(state["verification_failure"]),
            },
        ))
        ctx.set_status(JobStatus.VERIFYING, JobStatus.FAILED_VERIFICATION)
        return {}

    return node
