from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.knowledge import KnowledgeType


# ─────────────────────────────────────────────────────────────────────────────
# create_document
# ─────────────────────────────────────────────────────────────────────────────

def test_create_document_persists_document_with_correct_fields(
    knowledge_routes_with_mocks,
    fake_cursor,
    test_store,
):
    # Given
    from app.schemas.knowledge import KnowledgeDocumentCreate

    body = KnowledgeDocumentCreate(
        content="Example plan content",
        doc_type=KnowledgeType.PLAN,
        title="Test Plan",
    )

    # When
    response = knowledge_routes_with_mocks.create_document(body, cursor=fake_cursor)

    # Then
    assert response.document.content == "Example plan content"
    assert response.document.doc_type == KnowledgeType.PLAN
    assert response.document.title == "Test Plan"
    assert response.document.document_id in test_store["knowledge"]


def test_create_document_persists_code_type_document(
    knowledge_routes_with_mocks,
    fake_cursor,
    test_store,
):
    # Given
    from app.schemas.knowledge import KnowledgeDocumentCreate

    body = KnowledgeDocumentCreate(
        content="from manim import *",
        doc_type=KnowledgeType.CODE,
        title="Scene1 example",
    )

    # When
    response = knowledge_routes_with_mocks.create_document(body, cursor=fake_cursor)

    # Then
    assert response.document.doc_type == KnowledgeType.CODE
    assert response.document.document_id in test_store["knowledge"]


# ─────────────────────────────────────────────────────────────────────────────
# get_document
# ─────────────────────────────────────────────────────────────────────────────

def test_get_document_returns_matching_document(
    knowledge_routes_with_mocks,
    fake_cursor,
):
    # Given
    from app.schemas.knowledge import KnowledgeDocumentCreate

    body = KnowledgeDocumentCreate(
        content="Some code example",
        doc_type=KnowledgeType.CODE,
        title="Test Code",
    )
    create_response = knowledge_routes_with_mocks.create_document(body, cursor=fake_cursor)
    doc_id = create_response.document.document_id

    # When
    response = knowledge_routes_with_mocks.get_document(doc_id, cursor=fake_cursor)

    # Then
    assert response.document.document_id == doc_id
    assert response.document.content == "Some code example"
    assert response.document.doc_type == KnowledgeType.CODE


def test_get_document_raises_404_when_document_not_found(
    knowledge_routes_with_mocks,
    fake_cursor,
):
    # Given
    missing_id = uuid4()

    # When / Then
    with pytest.raises(HTTPException) as exc_info:
        knowledge_routes_with_mocks.get_document(missing_id, cursor=fake_cursor)

    assert exc_info.value.status_code == 404
    assert "Document not found" in exc_info.value.detail


# ─────────────────────────────────────────────────────────────────────────────
# delete_document
# ─────────────────────────────────────────────────────────────────────────────

def test_delete_document_removes_document_from_store(
    knowledge_routes_with_mocks,
    fake_cursor,
    test_store,
):
    # Given
    from app.schemas.knowledge import KnowledgeDocumentCreate

    body = KnowledgeDocumentCreate(
        content="To be deleted",
        doc_type=KnowledgeType.PLAN,
        title="Delete Me",
    )
    create_response = knowledge_routes_with_mocks.create_document(body, cursor=fake_cursor)
    doc_id = create_response.document.document_id
    assert doc_id in test_store["knowledge"]

    # When
    knowledge_routes_with_mocks.delete_document(doc_id, cursor=fake_cursor)

    # Then
    assert doc_id not in test_store["knowledge"]


def test_delete_document_raises_404_when_document_not_found(
    knowledge_routes_with_mocks,
    fake_cursor,
):
    # Given
    missing_id = uuid4()

    # When / Then
    with pytest.raises(HTTPException) as exc_info:
        knowledge_routes_with_mocks.delete_document(missing_id, cursor=fake_cursor)

    assert exc_info.value.status_code == 404
    assert "Document not found" in exc_info.value.detail


# ─────────────────────────────────────────────────────────────────────────────
# get_documents (by type)
# ─────────────────────────────────────────────────────────────────────────────

def test_get_documents_by_type_returns_only_matching_type(
    knowledge_routes_with_mocks,
    fake_cursor,
):
    # Given
    from app.schemas.knowledge import KnowledgeDocumentCreate

    knowledge_routes_with_mocks.create_document(
        KnowledgeDocumentCreate(content="Plan content", doc_type=KnowledgeType.PLAN, title="Plan Doc"),
        cursor=fake_cursor,
    )
    knowledge_routes_with_mocks.create_document(
        KnowledgeDocumentCreate(content="Code content", doc_type=KnowledgeType.CODE, title="Code Doc"),
        cursor=fake_cursor,
    )

    # When
    response = knowledge_routes_with_mocks.get_documents(
        doc_type=KnowledgeType.PLAN, cursor=fake_cursor
    )

    # Then
    assert len(response.documents) == 1
    assert response.documents[0].doc_type == KnowledgeType.PLAN
    assert response.documents[0].content == "Plan content"


def test_get_documents_by_type_returns_empty_list_when_none_of_that_type_exist(
    knowledge_routes_with_mocks,
    fake_cursor,
):
    # Given — empty knowledge store

    # When
    response = knowledge_routes_with_mocks.get_documents(
        doc_type=KnowledgeType.CODE, cursor=fake_cursor
    )

    # Then
    assert response.documents == []
