import time
from collections import Counter

from langchain_core.messages import HumanMessage, SystemMessage

from lab_logging import LabLog
from runtime.context import ExperimentContext
from schemas import CodePlan, VideoPlan
from settings import (
    CODE_PLAN_OUTPUT_MAX_TOKENS,
    OPENROUTER_CODE_PLAN_MODEL,
    ArchivedPromptFiles,
    LogFileNames,
    PromptFiles,
    UsageFileNames,
)
from workflow_state import NodeName, WorkflowState


def make_generate_code_plan_node(ctx: ExperimentContext, name: NodeName):
    operation = name.value

    def node(state: WorkflowState) -> dict:
        ctx.run_logger.info(LabLog(operation=operation, event="Node started"))
        plan = state["plan"]
        if plan is None:
            raise RuntimeError("Cannot generate a code plan without a video plan.")
        required_scene_numbers = _required_scene_numbers(plan)
        if not required_scene_numbers:
            raise RuntimeError(
                "Cannot generate a code plan because the video plan has no "
                "renderable scenes."
            )

        ctx.files.archive_prompt_file(
            PromptFiles.CODE_PLAN_SYSTEM,
            ArchivedPromptFiles.GENERATE_CODE_PLAN_SYSTEM,
        )

        plan_prompt_text = plan.to_prompt_text()
        user_prompt = _build_user_prompt(
            request_text=state["request_text"],
            plan_json=plan_prompt_text,
            required_scene_numbers=required_scene_numbers,
        )
        ctx.files.write_prompt(
            ArchivedPromptFiles.GENERATE_CODE_PLAN_USER,
            user_prompt,
        )

        ctx.run_logger.info(LabLog(
            operation=operation,
            event="OpenRouter call started",
            context={
                "model": OPENROUTER_CODE_PLAN_MODEL,
                "max_tokens": CODE_PLAN_OUTPUT_MAX_TOKENS,
                "plan_chars": len(plan_prompt_text),
            },
        ))
        started_at = time.perf_counter()
        code_plan, usage = ctx.llm.invoke_structured(
            model=OPENROUTER_CODE_PLAN_MODEL,
            messages=[
                SystemMessage(
                    content=ctx.files.read_prompt(PromptFiles.CODE_PLAN_SYSTEM).strip()
                ),
                *state["messages"],
                HumanMessage(content=user_prompt),
            ],
            schema=CodePlan,
            max_tokens=CODE_PLAN_OUTPUT_MAX_TOKENS,
            reasoning_effort=None,
        )
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        code_plan_prompt_text = code_plan.to_prompt_text()
        ctx.files.save_code_plan(code_plan)
        validation_warnings = _validate_code_plan(
            code_plan=code_plan,
            required_scene_numbers=required_scene_numbers,
        )
        cumulative_usage = ctx.usage.record(
            UsageFileNames.GENERATE_CODE_PLAN,
            usage,
            duration_ms,
        )
        ctx.usage.log_llm_completed(
            ctx.run_logger,
            operation=operation,
            model=OPENROUTER_CODE_PLAN_MODEL,
            duration_ms=duration_ms,
            usage=usage,
            cumulative_usage=cumulative_usage,
            extra_context={
                "scene_blueprint_count": len(code_plan.scenes),
                "code_plan_chars": len(code_plan_prompt_text),
                "validation_warning_count": len(validation_warnings),
            },
        )
        if validation_warnings:
            actual_scene_numbers = [
                scene.scene_number for scene in code_plan.scenes
            ]
            ctx.files.write_log_json(
                LogFileNames.CODE_PLAN_VALIDATION_ERROR,
                {
                    "expected_scene_numbers": required_scene_numbers,
                    "actual_scene_numbers": actual_scene_numbers,
                    "warnings": validation_warnings,
                },
            )
            ctx.run_logger.warning(LabLog(
                operation=operation,
                event="Code plan validation warnings",
                context={
                    "expected_scene_numbers": required_scene_numbers,
                    "actual_scene_numbers": actual_scene_numbers,
                    "warning_count": len(validation_warnings),
                },
            ))
        return {"code_plan": code_plan}

    return node


def _build_user_prompt(
    *,
    request_text: str,
    plan_json: str,
    required_scene_numbers: list[int],
) -> str:
    return (
        "Create a Manim code implementation plan for this lesson.\n\n"
        f"Required scene_number values: {required_scene_numbers}\n\n"
        "Teacher request:\n"
        f"{request_text}\n\n"
        "Video plan JSON:\n"
        f"{plan_json}"
    )


def _required_scene_numbers(plan: VideoPlan) -> list[int]:
    return sorted({scene.scene_number for scene in plan.scenes if scene.scene_number >= 1})


def _validate_code_plan(
    *,
    code_plan: CodePlan,
    required_scene_numbers: list[int],
) -> list[str]:
    errors: list[str] = []
    expected = set(required_scene_numbers)
    actual_scene_numbers = [scene.scene_number for scene in code_plan.scenes]
    actual = set(actual_scene_numbers)

    duplicate_scene_numbers = sorted(
        scene_number
        for scene_number, count in Counter(actual_scene_numbers).items()
        if count > 1
    )
    if duplicate_scene_numbers:
        errors.append(
            "Duplicate code-plan scenes for scene_number(s): "
            f"{duplicate_scene_numbers}."
        )

    missing_scene_numbers = sorted(expected - actual)
    if missing_scene_numbers:
        errors.append(
            "Missing code-plan scenes for scene_number(s): "
            f"{missing_scene_numbers}."
        )

    extra_scene_numbers = sorted(actual - expected)
    if extra_scene_numbers:
        errors.append(
            "Unexpected code-plan scenes for scene_number(s): "
            f"{extra_scene_numbers}."
        )

    for scene in code_plan.scenes:
        if scene.subscenes and scene.subscenes[0].transition == "transform":
            errors.append(
                f"Scene {scene.scene_number} starts with transform subscene "
                f"'{scene.subscenes[0].id}'; the first subscene should show a "
                "snapshot because no previous main content exists."
            )

    return errors
