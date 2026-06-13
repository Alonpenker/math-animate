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


def test_registry_has_no_example_entries():
    from app.llm_knowledge.skill_documents import REGISTRY
    from app.schemas.knowledge import KnowledgeType

    examples = [e for e in REGISTRY if e.doc_type == KnowledgeType.EXAMPLE]
    assert examples == [], f"Registry must have no example entries, found: {[e.title for e in examples]}"


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


def test_registry_has_exactly_11_template_entries():
    from app.llm_knowledge.skill_documents import REGISTRY
    from app.schemas.knowledge import KnowledgeType, TemplateDocumentSeed

    templates = [e for e in REGISTRY if e.doc_type == KnowledgeType.TEMPLATE]
    assert len(templates) == 11, f"Expected 11 templates, got {len(templates)}: {[t.title for t in templates]}"
    for t in templates:
        assert isinstance(t, TemplateDocumentSeed), f"{t.title!r} has doc_type=TEMPLATE but is not a TemplateDocumentSeed"


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


def test_template_titles_constant_matches_template_registry_entries():
    from app.llm_knowledge.skill_documents import REGISTRY, TEMPLATE_TITLES
    from app.schemas.knowledge import KnowledgeType

    registry_template_titles = tuple(
        e.title for e in REGISTRY if e.doc_type == KnowledgeType.TEMPLATE
    )
    assert TEMPLATE_TITLES == registry_template_titles
    assert len(TEMPLATE_TITLES) == 11


def test_core_documents_contains_manim_skill_overview_and_visual_kit_api():
    from app.llm_knowledge.skill_documents import CORE_DOCUMENTS

    core_titles = {doc.title for doc in CORE_DOCUMENTS}
    assert "Manim Skill Overview" in core_titles
    assert "Visual Kit API" in core_titles
    assert len(CORE_DOCUMENTS) == 2, f"Expected 2 core documents, got {len(CORE_DOCUMENTS)}: {[d.title for d in CORE_DOCUMENTS]}"


def test_all_templates_have_non_empty_planning_capability():
    from app.llm_knowledge.skill_documents import REGISTRY
    from app.schemas.knowledge import KnowledgeType, TemplateDocumentSeed

    templates = [e for e in REGISTRY if e.doc_type == KnowledgeType.TEMPLATE]
    for t in templates:
        assert isinstance(t, TemplateDocumentSeed), f"{t.title!r} is TEMPLATE but not TemplateDocumentSeed"
        assert t.planning_capability.strip(), f"{t.title!r} has empty planning_capability"


def test_coding_model_is_gpt_oss_120b():
    from app.configs.llm_settings import OPENROUTER_MODELS

    assert OPENROUTER_MODELS.CODING_MODEL == "openai/gpt-oss-120b:free"
