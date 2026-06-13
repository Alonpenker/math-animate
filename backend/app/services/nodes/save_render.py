import shutil
import tempfile
from pathlib import Path

from app.domain.job_state import JobStatus
from app.schemas.artifact import ArtifactType
from app.schemas.jobs import Job, JobRequest
from app.services.nodes._context import CodegenContext
from app.utils.logging import Logger, WorkerLog
from app.workers.worker_helpers import get_storage, save_artifact_to_storage
from app.workers.worker_settings import PathNames

logger = Logger.get_logger("worker")

_NODE_NAME = "save_and_render"


def make_save_render_node(ctx: CodegenContext):
    def node(state) -> dict:
        ctx.log_node_started(_NODE_NAME)
        storage = get_storage()
        job_dir = Path(PathNames.ARTIFACTS_FOLDER) / str(ctx.job_id)
        job_dir.mkdir(parents=True, exist_ok=True)
        try:
            with tempfile.NamedTemporaryFile(
                suffix=f".{ArtifactType.PYTHON_FILE.value}",
                dir=job_dir,
                delete=False,
            ) as tmp:
                tmp.write(state["code"].encode("utf-8"))
                file_path = Path(tmp.name)
            save_artifact_to_storage(ctx.job_id, file_path, ArtifactType.PYTHON_FILE, storage)
        finally:
            if job_dir.exists():
                shutil.rmtree(job_dir, ignore_errors=True)

        ctx.set_status(JobStatus.VERIFYING, JobStatus.VERIFIED)
        logger.info(WorkerLog(
            operation="generate_code",
            event="Verification completed and render enqueued",
            job_id=str(ctx.job_id),
        ))
        from app.workers.worker import generate_render
        generate_render.delay(
            JobRequest(job=Job(job_id=ctx.job_id, status=JobStatus.VERIFIED)).model_dump(mode="json")
        )
        return {}

    return node
