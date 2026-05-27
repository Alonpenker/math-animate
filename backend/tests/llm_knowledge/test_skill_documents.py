"""Tests for the knowledge document registry."""
from uuid import UUID


def test_registry_contains_no_duplicate_document_ids():
    from app.llm_knowledge.skill_documents import REGISTRY

    ids = [entry.document_id for entry in REGISTRY]
    assert len(ids) == len(set(ids)), "REGISTRY has duplicate document_ids"


def test_registry_by_id_matches_registry():
    from app.llm_knowledge.skill_documents import REGISTRY, REGISTRY_BY_ID

    assert len(REGISTRY_BY_ID) == len(REGISTRY)
    for entry in REGISTRY:
        assert REGISTRY_BY_ID[entry.document_id] is entry


def test_core_documents_are_subset_of_registry():
    from app.llm_knowledge.skill_documents import REGISTRY, CORE_DOCUMENTS

    registry_ids = {e.document_id for e in REGISTRY}
    for doc in CORE_DOCUMENTS:
        assert doc.document_id in registry_ids


def test_core_documents_all_have_core_priority():
    from app.llm_knowledge.skill_documents import CORE_DOCUMENTS

    for doc in CORE_DOCUMENTS:
        assert doc.priority == "core", f"{doc.title!r} is in CORE_DOCUMENTS but priority={doc.priority!r}"


def test_all_rule_categories_are_enum_instances():
    from app.llm_knowledge.skill_documents import REGISTRY
    from app.llm_knowledge.categories import RuleCategory
    from app.schemas.knowledge import KnowledgeType

    rules = [e for e in REGISTRY if e.doc_type == KnowledgeType.RULE]
    for entry in rules:
        assert isinstance(entry.category, RuleCategory), (
            f"Rule {entry.title!r} has category={entry.category!r}, expected a RuleCategory enum"
        )


def test_all_example_categories_are_enum_instances():
    from app.llm_knowledge.skill_documents import REGISTRY
    from app.llm_knowledge.categories import ExampleCategory
    from app.schemas.knowledge import KnowledgeType

    examples = [e for e in REGISTRY if e.doc_type == KnowledgeType.EXAMPLE]
    assert len(examples) > 0, "No examples registered"
    for entry in examples:
        assert isinstance(entry.category, ExampleCategory), (
            f"Example {entry.title!r} has category={entry.category!r}, expected an ExampleCategory enum"
        )


def test_all_template_categories_are_enum_instances():
    from app.llm_knowledge.skill_documents import REGISTRY
    from app.llm_knowledge.categories import TemplateCategory
    from app.schemas.knowledge import KnowledgeType

    templates = [e for e in REGISTRY if e.doc_type == KnowledgeType.TEMPLATE]
    assert len(templates) > 0, "No templates registered"
    for entry in templates:
        assert isinstance(entry.category, TemplateCategory), (
            f"Template {entry.title!r} has category={entry.category!r}, expected a TemplateCategory enum"
        )


def test_all_registered_file_paths_exist():
    from app.llm_knowledge.skill_documents import REGISTRY, LLMKNOWLEDGE_DIR

    missing = [
        entry.path
        for entry in REGISTRY
        if not (LLMKNOWLEDGE_DIR / entry.path).exists()
    ]
    assert missing == [], f"Missing knowledge files: {missing}"


def test_registry_has_at_least_one_example_per_example_category():
    from app.llm_knowledge.skill_documents import REGISTRY
    from app.llm_knowledge.categories import ExampleCategory
    from app.schemas.knowledge import KnowledgeType

    registered_categories = {
        e.category
        for e in REGISTRY
        if e.doc_type == KnowledgeType.EXAMPLE
    }
    for cat in ExampleCategory:
        assert cat in registered_categories, f"No example registered for category {cat.value!r}"


def test_layout_composition_rule_uses_visual_layout_category():
    from app.llm_knowledge.skill_documents import REGISTRY
    from app.llm_knowledge.categories import RuleCategory

    entry = next((e for e in REGISTRY if e.title == "Layout Composition"), None)
    assert entry is not None, "Layout Composition rule not found in REGISTRY"
    assert entry.category == RuleCategory.VISUAL_LAYOUT


def test_no_legacy_string_categories_in_rules():
    """All rule documents must use RuleCategory enum values, not raw strings."""
    from app.llm_knowledge.skill_documents import REGISTRY
    from app.llm_knowledge.categories import RuleCategory
    from app.schemas.knowledge import KnowledgeType

    for entry in REGISTRY:
        if entry.doc_type == KnowledgeType.RULE:
            assert isinstance(entry.category, RuleCategory), (
                f"Rule {entry.title!r} uses legacy string category {entry.category!r}"
            )
