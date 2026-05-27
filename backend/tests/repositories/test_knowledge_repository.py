import numpy as np
import pytest
from uuid import uuid4

from app.llm_knowledge.categories import ExampleCategory, RuleCategory, SkillCategory, TemplateCategory
from app.llm_knowledge.skill_documents import LLMKNOWLEDGE_DIR, REGISTRY
from app.repositories.knowledge_repository import KnowledgeRepository
from app.schemas.knowledge import (
    KnowledgeDocument,
    KnowledgeDocumentSchema,
    KnowledgeDocumentSeed,
    KnowledgeType,
)

from tests.repositories.conftest import FakeSqlCursor

def _doc_row(document_id=None, doc_type: str = "rule") -> dict:
    return {
        "document_id": str(document_id or uuid4()),
        "doc_type": doc_type,
        "title": "Sample Title",
        "category": RuleCategory.GENERAL.value,
        "priority": "recommended",
        "tags": ["foo"],
    }

def test_skill_document_registry_paths_ids_and_titles_are_integral():
    paths = [entry.path for entry in REGISTRY]
    document_ids = [entry.document_id for entry in REGISTRY]
    titles = [entry.title for entry in REGISTRY]

    assert all((LLMKNOWLEDGE_DIR / path).exists() for path in paths)
    assert len(document_ids) == len(set(document_ids))
    assert len(titles) == len(set(titles))

def test_registered_rule_files_have_front_matter_and_cover_rules_directory():
    rule_paths = {
        entry.path
        for entry in REGISTRY
        if entry.doc_type == KnowledgeType.RULE
    }
    actual_rule_paths = {
        path.relative_to(LLMKNOWLEDGE_DIR).as_posix()
        for path in (LLMKNOWLEDGE_DIR / "manim_skill/rules").glob("*.md")
    }

    assert actual_rule_paths == rule_paths

    for path in rule_paths:
        content = (LLMKNOWLEDGE_DIR / path).read_text(encoding="utf-8")
        assert content.splitlines()[0] == "---"

def test_knowledge_type_enum_has_exactly_four_values():
    values = {member.value for member in KnowledgeType}

    assert values == {"skill", "rule", "template", "example"}
    assert len(list(KnowledgeType)) == 4

def test_knowledge_document_validates_with_metadata_only_no_content_or_path():
    doc = KnowledgeDocument(
        document_id=uuid4(),
        doc_type=KnowledgeType.RULE,
        title="A rule",
        category=RuleCategory.GENERAL,
    )

    assert doc.category == RuleCategory.GENERAL
    assert doc.priority == "optional"
    assert doc.tags == []
    assert "content" not in KnowledgeDocument.model_fields
    assert "path" not in KnowledgeDocument.model_fields

def test_knowledge_document_priority_rejects_unlisted_strings():
    with pytest.raises(Exception):
        KnowledgeDocument(
            document_id=uuid4(),
            doc_type=KnowledgeType.RULE,
            title="Bad priority",
            priority="urgent",  # not in PriorityType literal
        )

def test_knowledge_document_seed_requires_path_and_has_no_content():
    seed = KnowledgeDocumentSeed(
        document_id=uuid4(),
        doc_type=KnowledgeType.SKILL,
        title="Seed",
        priority="core",
        category=SkillCategory.CORE,
        path="manim_skill/SKILL.md",
    )

    assert seed.path == "manim_skill/SKILL.md"
    assert "content" not in KnowledgeDocumentSeed.model_fields

    with pytest.raises(Exception):
        KnowledgeDocumentSeed(
            document_id=uuid4(),
            doc_type=KnowledgeType.SKILL,
            title="No path",
            priority="core",
            category=SkillCategory.CORE,
        )

def test_knowledge_document_schema_has_exactly_seven_columns_with_no_content_or_path():
    column_attrs = {
        name: value
        for name, value in vars(KnowledgeDocumentSchema).items()
        if name.isupper() and not name.startswith("_")
    }
    column_names = {col.name for col in column_attrs.values()}

    assert len(column_attrs) == 7
    assert column_names == {
        "document_id", "doc_type", "priority",
        "title", "category", "embedding", "tags",
    }
    assert "CONTENT" not in vars(KnowledgeDocumentSchema)
    assert "PATH" not in vars(KnowledgeDocumentSchema)
    assert KnowledgeDocumentSchema.TAGS.type == "TEXT[]"

def test_create_document_executes_insert_with_seven_params_and_no_content():
    # Given
    cursor = FakeSqlCursor()
    document_id = uuid4()
    embedding = np.zeros(768, dtype=np.float32)

    # When
    KnowledgeRepository.create_document(
        cursor,
        document_id=document_id,
        doc_type="rule",
        title="Quadratic Formula",
        embedding=embedding,
        category=RuleCategory.GENERAL,
        priority="recommended",
        tags=["math", "algebra"],
    )

    # Then
    assert len(cursor.queries) == 1
    _, params = cursor.queries[0]
    assert len(params) == 7
    assert params[0] == str(document_id)
    assert params[1] == "rule"
    assert params[2] == "recommended"
    assert params[3] == "Quadratic Formula"
    assert params[4] == RuleCategory.GENERAL
    assert params[5] is embedding
    assert params[6] == ["math", "algebra"]

def test_create_document_defaults_tags_to_empty_list_when_none():
    cursor = FakeSqlCursor()
    embedding = np.zeros(768, dtype=np.float32)

    KnowledgeRepository.create_document(
        cursor,
        document_id=uuid4(),
        doc_type="rule",
        title="Default tags",
        embedding=embedding,
        category=RuleCategory.GENERAL,
    )

    _, params = cursor.queries[0]
    assert params[6] == []
    assert params[2] == "optional"
    assert params[4] == RuleCategory.GENERAL

def test_get_document_returns_knowledge_document_when_row_exists():
    # Given
    document_id = uuid4()
    cursor = FakeSqlCursor(rows=[_doc_row(document_id=document_id, doc_type="rule")])

    # When
    result = KnowledgeRepository.get_document(cursor, document_id)

    # Then
    assert result is not None
    assert str(result.document_id) == str(document_id)
    assert result.doc_type == KnowledgeType.RULE
    assert result.title == "Sample Title"
    assert result.category == RuleCategory.GENERAL
    assert result.priority == "recommended"
    assert result.tags == ["foo"]

def test_get_document_returns_none_when_no_row_found():
    # Given
    cursor = FakeSqlCursor(rows=[])

    # When
    result = KnowledgeRepository.get_document(cursor, uuid4())

    # Then
    assert result is None

def test_delete_document_returns_true_when_row_was_deleted():
    # Given
    cursor = FakeSqlCursor(rowcount=1)

    # When
    result = KnowledgeRepository.delete_document(cursor, uuid4())

    # Then
    assert result is True

def test_delete_document_returns_false_when_no_row_was_deleted():
    # Given
    cursor = FakeSqlCursor(rowcount=0)

    # When
    result = KnowledgeRepository.delete_document(cursor, uuid4())

    # Then
    assert result is False

def test_document_exists_returns_true_when_row_found():
    # Given
    cursor = FakeSqlCursor(rows=[_doc_row()])

    # When
    result = KnowledgeRepository.document_exists(cursor, uuid4())

    # Then
    assert result is True

def test_document_exists_returns_false_when_no_row_found():
    # Given
    cursor = FakeSqlCursor(rows=[])

    # When
    result = KnowledgeRepository.document_exists(cursor, uuid4())

    # Then
    assert result is False

def test_search_similar_returns_list_of_knowledge_documents():
    # Given
    rows = [_doc_row(doc_type="rule"), _doc_row(doc_type="rule")]
    cursor = FakeSqlCursor(rows=rows)
    embedding = np.zeros(768, dtype=np.float32)

    # When
    results = KnowledgeRepository.search_similar(cursor, embedding, doc_type="rule", limit=2)

    # Then
    assert len(results) == 2
    assert all(isinstance(doc, KnowledgeDocument) for doc in results)
    assert all(doc.doc_type == KnowledgeType.RULE for doc in results)

def test_search_similar_returns_empty_list_when_no_matches():
    # Given
    cursor = FakeSqlCursor(rows=[])
    embedding = np.zeros(768, dtype=np.float32)

    # When
    results = KnowledgeRepository.search_similar(cursor, embedding, doc_type="rule", limit=5)

    # Then
    assert results == []
