"""
KnowledgeRepository tests.

Uses FakeSqlCursor to verify SQL interactions and domain object construction
for knowledge document CRUD and vector similarity search operations.
"""
import numpy as np
from uuid import uuid4

from app.repositories.knowledge_repository import KnowledgeRepository
from app.schemas.knowledge import KnowledgeDocument, KnowledgeType

from tests.repositories.conftest import FakeSqlCursor


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _doc_row(document_id=None, doc_type: str = "plan") -> dict:
    return {
        "document_id": str(document_id or uuid4()),
        "content": "Sample knowledge content",
        "doc_type": doc_type,
        "title": "Sample Title",
    }


# ─────────────────────────────────────────────────────────────────────────────
# KnowledgeRepository.create_document
# ─────────────────────────────────────────────────────────────────────────────

def test_create_document_executes_insert_with_all_required_fields():
    # Given
    cursor = FakeSqlCursor()
    document_id = uuid4()
    embedding = np.zeros(768, dtype=np.float32)

    # When
    KnowledgeRepository.create_document(
        cursor,
        document_id=document_id,
        content="Quadratic formula derivation",
        doc_type="plan",
        title="Quadratic Formula",
        embedding=embedding,
    )

    # Then
    assert len(cursor.queries) == 1
    _, params = cursor.queries[0]
    assert str(document_id) in params
    assert "Quadratic formula derivation" in params
    assert "plan" in params


# ─────────────────────────────────────────────────────────────────────────────
# KnowledgeRepository.get_document
# ─────────────────────────────────────────────────────────────────────────────

def test_get_document_returns_knowledge_document_when_row_exists():
    # Given
    document_id = uuid4()
    cursor = FakeSqlCursor(rows=[_doc_row(document_id=document_id, doc_type="plan")])

    # When
    result = KnowledgeRepository.get_document(cursor, document_id)

    # Then
    assert result is not None
    assert str(result.document_id) == str(document_id)
    assert result.doc_type == KnowledgeType.PLAN
    assert result.content == "Sample knowledge content"


def test_get_document_returns_none_when_no_row_found():
    # Given
    cursor = FakeSqlCursor(rows=[])

    # When
    result = KnowledgeRepository.get_document(cursor, uuid4())

    # Then
    assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# KnowledgeRepository.delete_document
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# KnowledgeRepository.document_exists
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# KnowledgeRepository.search_similar
# ─────────────────────────────────────────────────────────────────────────────

def test_search_similar_returns_list_of_knowledge_documents():
    # Given
    rows = [_doc_row(doc_type="plan"), _doc_row(doc_type="plan")]
    cursor = FakeSqlCursor(rows=rows)
    embedding = np.zeros(768, dtype=np.float32)

    # When
    results = KnowledgeRepository.search_similar(cursor, embedding, doc_type="plan", limit=2)

    # Then
    assert len(results) == 2
    assert all(isinstance(doc, KnowledgeDocument) for doc in results)
    assert all(doc.doc_type == KnowledgeType.PLAN for doc in results)


def test_search_similar_returns_empty_list_when_no_matches():
    # Given
    cursor = FakeSqlCursor(rows=[])
    embedding = np.zeros(768, dtype=np.float32)

    # When
    results = KnowledgeRepository.search_similar(cursor, embedding, doc_type="plan", limit=5)

    # Then
    assert results == []
