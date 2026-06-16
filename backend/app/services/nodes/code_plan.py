import time

from langchain_core.messages import HumanMessage, SystemMessage

from app.configs.llm_settings import (
    CODE_PLAN_SYSTEM_PROMPT,
    LLM_CODE_PLAN_OUTPUT_MAX_TOKENS,
    OPENROUTER_MODELS,
)
from app.llm_knowledge.skill_documents import REGISTRY
from app.schemas.code_plan import CodePlan
from app.schemas.knowledge import TemplateDocumentSeed
from app.services.nodes._context import CodegenContext
from app.services.openrouter_service import CallType, OpenRouterService
from app.utils.logging import Logger, WorkerLog

logger = Logger.get_logger("worker")

_NODE_NAME = "generate_code_plan"


def make_code_plan_node(ctx: CodegenContext):
    def node(state) -> dict:
        ctx.log_node_started(_NODE_NAME)
        plan = state["plan"]
        plan_text = plan.to_prompt_text()
        user_request_text = str(state["user_request"])

        required_scene_numbers = sorted({
            scene.scene_number for scene in plan.scenes if scene.scene_number >= 1
        })

        user_prompt = (
            "Create a Manim code implementation plan for this lesson.\n\n"
            f"Required scene_number values: {required_scene_numbers}\n\n"
            "Teacher request:\n"
            f"{user_request_text}\n\n"
            "Video plan JSON:\n"
            f"{plan_text}"
        )

        knowledge_messages = [
            msg for msg in state["messages"] if isinstance(msg, SystemMessage)
        ]

        started_at = time.perf_counter()
        code_plan, usage = OpenRouterService.invoke_structured(
            job_id=ctx.job_id,
            stage=ctx.current_status,
            call_type=CallType.CODE_PLAN,
            model=OPENROUTER_MODELS.CODE_PLAN_MODEL,
            messages=[
                SystemMessage(content=CODE_PLAN_SYSTEM_PROMPT.strip()),
                *knowledge_messages,
                HumanMessage(content=user_prompt),
            ],
            schema=CodePlan,
            max_tokens=LLM_CODE_PLAN_OUTPUT_MAX_TOKENS,
        )
        referenced_templates = _resolve_referenced_templates(code_plan)
        ctx.log_openrouter_call(
            CallType.CODE_PLAN,
            started_at,
            usage,
            {
                "scene_blueprint_count": len(code_plan.scenes),
                "referenced_template_count": len(referenced_templates),
            },
            model=OPENROUTER_MODELS.CODE_PLAN_MODEL,
        )
        logger.info(WorkerLog(
            operation="generate_code",
            event="Code plan generated",
            job_id=str(ctx.job_id),
            context={
                "scene_count": len(code_plan.scenes),
                "referenced_templates": [t.title for t in referenced_templates],
            },
        ))
        return {
            "code_plan": code_plan,
            "referenced_templates": referenced_templates,
        }

    return node


def _resolve_referenced_templates(code_plan: CodePlan) -> list[TemplateDocumentSeed]:
    registry_by_title = {entry.title: entry for entry in REGISTRY}
    referenced: list[TemplateDocumentSeed] = []
    seen_ids: set = set()
    for scene in code_plan.scenes:
        for subscene in scene.subscenes:
            for template in subscene.templates:
                doc = registry_by_title.get(template.reference)
                if (
                    doc is not None
                    and isinstance(doc, TemplateDocumentSeed)
                    and doc.document_id not in seen_ids
                ):
                    seen_ids.add(doc.document_id)
                    referenced.append(doc)
    return referenced
