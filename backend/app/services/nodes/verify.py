import shutil
from pathlib import Path

from app.domain.job_state import JobStatus
from app.services.nodes._assemble import extract_lesson_body
from app.services.nodes._context import CodegenContext
from app.utils.logging import Logger, WorkerLog
from app.workers.worker_helpers import (
    dry_run_docker,
    summarize_verification_failure,
    verify_code,
)
from app.workers.worker_settings import PathNames

logger = Logger.get_logger("worker")

_NODE_NAME = "verify"


def make_verify_node(ctx: CodegenContext):
    def node(state) -> dict:
        ctx.log_node_started(_NODE_NAME)
        expected_from = JobStatus.CODED if state["fix_attempt"] == 0 else JobStatus.FIXING
        ctx.set_status(expected_from, JobStatus.VERIFYING)

        render_root = Path(PathNames.TMP_RENDER_FOLDER)
        input_dir = render_root / str(ctx.job_id) / PathNames.INPUT_FOLDER
        input_dir.mkdir(parents=True, exist_ok=True)
        code_path = input_dir / PathNames.MANIM_CODE
        code_path.write_text(state["code"], encoding="utf-8")

        try:
            lesson_body = extract_lesson_body(state["code"])
            failure = verify_code(
                lesson_body,
                expected_scene_count=len(state["plan"].scenes),
            )
            is_fixable = True

            if failure is None:
                media_dir = input_dir / PathNames.MEDIA_FOLDER
                media_dir.mkdir(parents=True, exist_ok=True)
                media_dir.chmod(0o777)
                passed, error_output, is_fixable = dry_run_docker(code_path, media_dir)
                if not passed:
                    failure = (
                        f"Dry-run failed:\n{error_output}"
                        if is_fixable
                        else f"Dry-run infrastructure error:\n{error_output}"
                    )

            if failure is None:
                logger.info(WorkerLog(
                    operation="generate_code",
                    event="Verification passed",
                    job_id=str(ctx.job_id),
                    context={"fix_attempt": state["fix_attempt"]},
                ))
                return {"verification_failure": "", "verification_fixable": True}

            failure_summary = summarize_verification_failure(failure)
            logger.warning(WorkerLog(
                operation="generate_code",
                event="Verification failed",
                job_id=str(ctx.job_id),
                context={
                    "fix_attempt": state["fix_attempt"],
                    "failure_summary": failure_summary,
                    "is_fixable": is_fixable,
                },
            ))
            return {"verification_failure": failure, "verification_fixable": is_fixable}
        except Exception:
            ctx.set_status(JobStatus.VERIFYING, JobStatus.FAILED_VERIFICATION)
            raise
        finally:
            shutil.rmtree(input_dir, ignore_errors=True)

    return node
