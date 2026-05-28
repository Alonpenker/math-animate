from dataclasses import dataclass

from langchain_core.messages import SystemMessage

from llm_knowledge.skill_documents import CORE_DOCUMENTS, REGISTRY, read_knowledge_file
from schemas import KnowledgeDocumentSeed
from settings import DEFAULT_SELECTED_DOCUMENT_TITLES


@dataclass(frozen=True)
class KnowledgeBundle:
    messages: list[SystemMessage]
    metadata: dict[str, list[dict[str, str | list[str]]]]
    selected_titles: list[str]


def load_static_knowledge(codegen_system_prompt: str) -> KnowledgeBundle:
    registry_by_title = {entry.title: entry for entry in REGISTRY}

    selected_docs: list[KnowledgeDocumentSeed] = []
    for title in DEFAULT_SELECTED_DOCUMENT_TITLES:
        doc = registry_by_title.get(title)
        if doc is not None:
            selected_docs.append(doc)

    core_ids = {doc.document_id for doc in CORE_DOCUMENTS}
    selected_docs = [doc for doc in selected_docs if doc.document_id not in core_ids]

    core_content = "\n\n".join(read_knowledge_file(doc.path) for doc in CORE_DOCUMENTS)
    selected_sections = [
        f"# {doc.title}\n\n{read_knowledge_file(doc.path)}"
        for doc in selected_docs
    ]
    selected_content = (
        "\n\n".join(selected_sections)
        if selected_sections
        else "(No selected optional skill documents.)"
    )

    metadata = {
        "core_documents": [_doc_metadata(doc) for doc in CORE_DOCUMENTS],
        "selected_documents": [_doc_metadata(doc) for doc in selected_docs],
    }
    messages = [
        SystemMessage(content=codegen_system_prompt.strip()),
        SystemMessage(content=f"# Core Skill Documents\n\n{core_content}"),
        SystemMessage(content=f"# Selected Skill Documents\n\n{selected_content}"),
    ]
    return KnowledgeBundle(
        messages=messages,
        metadata=metadata,
        selected_titles=[doc.title for doc in selected_docs],
    )


def _doc_metadata(doc: KnowledgeDocumentSeed) -> dict[str, str | list[str]]:
    category = getattr(doc.category, "value", doc.category)
    return {
        "title": doc.title,
        "type": doc.doc_type.value,
        "category": str(category),
        "priority": doc.priority,
        "tags": doc.tags,
        "path": doc.path,
    }
