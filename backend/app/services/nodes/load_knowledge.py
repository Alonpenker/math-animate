from langchain_core.messages import SystemMessage

from app.configs.llm_settings import CODEGEN_SYSTEM_PROMPT
from app.llm_knowledge.skill_documents import CORE_DOCUMENTS, read_knowledge_file
from app.services.nodes._context import CodegenContext
from app.utils.logging import Logger, WorkerLog

logger = Logger.get_logger("worker")

_NODE_NAME = "load_selected_documents"


def make_load_knowledge_node(ctx: CodegenContext):
    def node(state) -> dict:
        ctx.log_node_started(_NODE_NAME)
        valid_titles = [t for t in ctx.selected_titles if t in ctx.candidates_by_title]
        invalid_titles = [t for t in ctx.selected_titles if t not in ctx.candidates_by_title]
        if invalid_titles:
            logger.warning(WorkerLog(
                operation="generate_code",
                event="Ignoring unknown selected skill document titles",
                job_id=str(ctx.job_id),
                context={"invalid_titles": invalid_titles},
            ))

        core_content = "\n\n".join(read_knowledge_file(doc.path) for doc in CORE_DOCUMENTS)

        document_sections = []
        for title in valid_titles:
            content = read_knowledge_file(ctx.candidates_by_title[title].path)
            document_sections.append(f"# {title}\n\n{content}")
        selected_content = (
            "\n\n".join(document_sections)
            if document_sections
            else "(No selected optional skill documents.)"
        )

        messages = [
            SystemMessage(content=CODEGEN_SYSTEM_PROMPT.strip()),
            SystemMessage(content=f"# Core Skill Documents\n\n{core_content}"),
            SystemMessage(
                content=(
                    "# Selected Skill Documents\n\n"
                    "Each section heading is its exact reference title. Code plans "
                    "record matching titles in `templates[].reference`; codegen and "
                    "fixing must use and preserve those validated build/action "
                    "contracts. Referenced template sources are prepended "
                    "authoritatively; use their template classes without copying, "
                    "redefining, or importing them. The active workflow contract "
                    "overrides reference scene classes and animation examples: do "
                    "not import references or copy direct `self.play(...)` "
                    "choreography.\n\n"
                    f"{selected_content}"
                )
            ),
        ]
        logger.info(WorkerLog(
            operation="generate_code",
            event="Selected skill documents loaded",
            job_id=str(ctx.job_id),
            context={
                "core_count": len(CORE_DOCUMENTS),
                "selected_count": len(valid_titles),
                "selected_titles": valid_titles,
            },
        ))
        return {"messages": messages}

    return node
