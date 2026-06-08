from dataclasses import dataclass

from langchain_core.messages import SystemMessage

from llm_knowledge.skill_documents import CORE_DOCUMENTS, REGISTRY, read_knowledge_file
from schemas import CodePlan, KnowledgeDocumentSeed, TemplateDocumentSeed
from settings import BASE_SELECTED_DOCUMENT_TITLES, STATIC_DOCUMENT_SELECTION_PROFILES


@dataclass(frozen=True)
class KnowledgeBundle:
    messages: list[SystemMessage]
    metadata: dict[str, list[dict[str, str | list[str]]]]
    selected_titles: list[str]


def load_planning_capabilities(*, request_text: str) -> str:
    registry_by_title = {entry.title: entry for entry in REGISTRY}
    capabilities = [
        doc.planning_capability
        for title in _select_document_titles(request_text=request_text, plan_text="")
        if (doc := registry_by_title.get(title)) is not None
        and isinstance(doc, TemplateDocumentSeed)
    ]
    if not capabilities:
        return ""
    return (
        "Validated visual capabilities available to the implementation stages:\n"
        + "\n".join(f"- {capability}" for capability in capabilities)
        + "\n\nUse these capabilities when they support the lesson, but keep the "
        "video plan human-readable. Do not mention templates, function names, "
        "classes, APIs, or implementation details."
    )


def load_static_knowledge(
    *,
    request_text: str,
    plan_text: str,
) -> KnowledgeBundle:
    registry_by_title = {entry.title: entry for entry in REGISTRY}

    selected_docs: list[KnowledgeDocumentSeed] = []
    for title in _select_document_titles(request_text=request_text, plan_text=plan_text):
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
    return KnowledgeBundle(
        messages=messages,
        metadata=metadata,
        selected_titles=[doc.title for doc in selected_docs],
    )


def resolve_referenced_templates(code_plan: CodePlan) -> list[KnowledgeDocumentSeed]:
    registry_by_title = {entry.title: entry for entry in REGISTRY}
    referenced_templates: list[KnowledgeDocumentSeed] = []
    seen_ids = set()
    for scene in code_plan.scenes:
        for subscene in scene.subscenes:
            for template in subscene.templates:
                title = template.reference
                doc = registry_by_title.get(title)
                if (
                    doc is not None
                    and isinstance(doc, TemplateDocumentSeed)
                    and doc.document_id not in seen_ids
                ):
                    seen_ids.add(doc.document_id)
                    referenced_templates.append(doc)
    return referenced_templates


def _select_document_titles(*, request_text: str, plan_text: str) -> list[str]:
    selected_titles = list(BASE_SELECTED_DOCUMENT_TITLES)
    searchable_text = f"{request_text}\n{plan_text}".lower()
    for keywords, titles in STATIC_DOCUMENT_SELECTION_PROFILES:
        if any(keyword in searchable_text for keyword in keywords):
            selected_titles.extend(titles)
            break
    return _dedupe_preserving_order(selected_titles)


def _dedupe_preserving_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


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
