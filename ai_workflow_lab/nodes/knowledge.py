from lab_logging import LabLog
from runtime.context import ExperimentContext
from services.knowledge_loader import load_static_knowledge
from settings import ArchivedPromptFiles, PromptFiles
from workflow_state import NodeName, WorkflowState


def make_load_static_knowledge_node(ctx: ExperimentContext, name: NodeName):
    operation = name.value

    def node(state: WorkflowState) -> dict:
        ctx.run_logger.info(LabLog(operation=operation, event="Node started"))
        ctx.files.archive_prompt_file(
            PromptFiles.CODEGEN_SYSTEM,
            ArchivedPromptFiles.GENERATE_CODE_SYSTEM,
        )
        bundle = load_static_knowledge(
            ctx.files.read_prompt(PromptFiles.CODEGEN_SYSTEM)
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
