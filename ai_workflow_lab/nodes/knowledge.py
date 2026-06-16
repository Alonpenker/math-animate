from lab_logging import LabLog
from runtime.context import ExperimentContext
from services.knowledge_loader import load_static_knowledge
from workflow_state import NodeName, WorkflowState


def make_load_static_knowledge_node(ctx: ExperimentContext, name: NodeName):
    operation = name.value

    def node(state: WorkflowState) -> dict:
        ctx.run_logger.info(LabLog(operation=operation, event="Node started"))
        plan = state["plan"]
        if plan is None:
            raise RuntimeError("Cannot load static knowledge without a validated plan.")
        bundle = load_static_knowledge(
            request_text=state["request_text"],
            plan_text=plan.to_prompt_text(),
        )
        ctx.files.write_selected_documents(bundle.metadata)
        ctx.run_logger.info(LabLog(
            operation=operation,
            event="Knowledge loaded",
            context={
                "core_count": len(bundle.metadata["core_documents"]),
                "selected_count": len(bundle.metadata["selected_documents"]),
                "selected_titles": bundle.selected_titles,
            },
        ))
        return {"messages": bundle.messages}

    return node
