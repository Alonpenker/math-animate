from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.knowledge import KnowledgeDocumentSchema, KnowledgeType


# ─────────────────────────────────────────────────────────────────────────────
# create_document
# ─────────────────────────────────────────────────────────────────────────────

def test_create_document_persists_document_with_correct_fields(
    knowledge_routes_with_mocks,
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
    response = knowledge_routes_with_mocks.create_document(request=object(), body=body)

    # Then
    assert "document_id" in response
    assert isinstance(response["document_id"], str)
    assert "message" in response
    assert len(response["message"]) > 0

    # Verify WorkerRunner.handle_create_document was called correctly
    assert len(test_store["worker_runner_calls"]) == 1
    call = test_store["worker_runner_calls"][0]
    assert call["content"] == "Example plan content"
    assert call["doc_type"] == KnowledgeType.PLAN.value
    assert call["title"] == "Test Plan"


def test_create_document_persists_code_type_document(
    knowledge_routes_with_mocks,
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
    response = knowledge_routes_with_mocks.create_document(request=object(), body=body)

    # Then
    assert "document_id" in response
    assert isinstance(response["document_id"], str)
    assert "message" in response
    assert len(response["message"]) > 0

    assert len(test_store["worker_runner_calls"]) == 1
    call = test_store["worker_runner_calls"][0]
    assert call["content"] == "from manim import *"
    assert call["doc_type"] == KnowledgeType.CODE.value
    assert call["title"] == "Scene1 example"


# ─────────────────────────────────────────────────────────────────────────────
# get_document
# ─────────────────────────────────────────────────────────────────────────────

def test_get_document_returns_matching_document(
    knowledge_routes_with_mocks,
    fake_cursor,
    test_store,
):
    # Given — seed knowledge store directly
    S = KnowledgeDocumentSchema
    doc_id = uuid4()
    test_store["knowledge"][doc_id] = {
        S.DOCUMENT_ID.name: doc_id,
        S.CONTENT.name: "Some code example",
        S.DOC_TYPE.name: KnowledgeType.CODE.value,
        S.TITLE.name: "Test Code",
    }

    # When
    response = knowledge_routes_with_mocks.get_document(
        request=object(), document_id=doc_id, cursor=fake_cursor
    )

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
        knowledge_routes_with_mocks.get_document(
            request=object(), document_id=missing_id, cursor=fake_cursor
        )

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
    # Given — seed knowledge store directly
    S = KnowledgeDocumentSchema
    doc_id = uuid4()
    test_store["knowledge"][doc_id] = {
        S.DOCUMENT_ID.name: doc_id,
        S.CONTENT.name: "To be deleted",
        S.DOC_TYPE.name: KnowledgeType.PLAN.value,
        S.TITLE.name: "Delete Me",
    }
    assert doc_id in test_store["knowledge"]

    # When
    knowledge_routes_with_mocks.delete_document(
        request=object(), document_id=doc_id, cursor=fake_cursor
    )

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
        knowledge_routes_with_mocks.delete_document(
            request=object(), document_id=missing_id, cursor=fake_cursor
        )

    assert exc_info.value.status_code == 404
    assert "Document not found" in exc_info.value.detail


# ─────────────────────────────────────────────────────────────────────────────
# get_documents (by type)
# ─────────────────────────────────────────────────────────────────────────────

def test_get_documents_by_type_returns_only_matching_type(
    knowledge_routes_with_mocks,
    fake_cursor,
    test_store,
):
    # Given — seed knowledge store directly
    S = KnowledgeDocumentSchema
    plan_id = uuid4()
    code_id = uuid4()
    test_store["knowledge"][plan_id] = {
        S.DOCUMENT_ID.name: plan_id,
        S.CONTENT.name: "Plan content",
        S.DOC_TYPE.name: KnowledgeType.PLAN.value,
        S.TITLE.name: "Plan Doc",
    }
    test_store["knowledge"][code_id] = {
        S.DOCUMENT_ID.name: code_id,
        S.CONTENT.name: "Code content",
        S.DOC_TYPE.name: KnowledgeType.CODE.value,
        S.TITLE.name: "Code Doc",
    }

    # When
    response = knowledge_routes_with_mocks.get_documents(
        request=object(), doc_type=KnowledgeType.PLAN, cursor=fake_cursor
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
        request=object(), doc_type=KnowledgeType.CODE, cursor=fake_cursor
    )

    # Then
    assert response.documents == []
