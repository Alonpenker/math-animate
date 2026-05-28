import time

from lab_logging import LabLog
from runtime.context import ExperimentContext
from settings import LogFileNames
from verify_render import render_docker
from workflow_state import NodeName, WorkflowState


def make_render_node(ctx: ExperimentContext, name: NodeName):
    operation = name.value

    def node(state: WorkflowState) -> dict:
        ctx.run_logger.info(LabLog(operation=operation, event="Node started"))
        final_code_path = ctx.files.save_final_code(state["code"])

        plan = state["plan"]
        if plan is None:
            raise RuntimeError("Cannot render without a validated plan.")
        scene_count = len([scene for scene in plan.scenes if scene.scene_number != -1])
        ctx.run_logger.info(LabLog(
            operation=operation,
            event="Docker render started",
            context={"scene_count": scene_count, "code_path": str(final_code_path)},
        ))
        started_at = time.perf_counter()
        output_files, stdout, stderr = render_docker(
            code_path=final_code_path,
            media_dir=ctx.files.media_dir,
            run_dir=ctx.files.run_dir,
            expected_scene_count=scene_count,
        )
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        ctx.files.write_log(LogFileNames.RENDER_STDOUT, stdout)
        ctx.files.write_log(LogFileNames.RENDER_STDERR, stderr)
        rendered_files = ctx.files.relative_paths(output_files)
        ctx.write_summary({
            "status": "rendered",
            "run_dir": str(ctx.files.run_dir),
            "fix_attempts": state["fix_attempt"],
            "rendered_files": rendered_files,
        })
        ctx.run_logger.info(LabLog(
            operation=operation,
            event="Render completed",
            context={
                "duration_ms": duration_ms,
                "video_count": len(rendered_files),
                "rendered_files": rendered_files,
            },
        ))
        return {"rendered_files": rendered_files}

    return node
