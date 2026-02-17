from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas.knowledge import KnowledgeType


def test_create_knowledge_document(
    knowledge_routes_with_mocks,
    fake_cursor,
    test_store,
):
    from app.schemas.knowledge import KnowledgeDocumentCreate

    body = KnowledgeDocumentCreate(
        content="Example plan content",
        doc_type=KnowledgeType.PLAN,
        title="Test Plan",
    )

    response = knowledge_routes_with_mocks.create_document(body, cursor=fake_cursor)

    assert response.document.content == "Example plan content"
    assert response.document.doc_type == KnowledgeType.PLAN
    assert response.document.title == "Test Plan"
    assert response.document.document_id in test_store["knowledge"]


def test_get_knowledge_document(
    knowledge_routes_with_mocks,
    fake_cursor,
    test_store,
):
    from app.schemas.knowledge import KnowledgeDocumentCreate, KnowledgeDocumentSchema

    body = KnowledgeDocumentCreate(
        content="Some code example",
        doc_type=KnowledgeType.CODE,
        title="Test Code",
    )
    create_response = knowledge_routes_with_mocks.create_document(body, cursor=fake_cursor)
    doc_id = create_response.document.document_id

    response = knowledge_routes_with_mocks.get_document(doc_id, cursor=fake_cursor)

    assert response.document.document_id == doc_id
    assert response.document.content == "Some code example"
    assert response.document.doc_type == KnowledgeType.CODE


def test_get_knowledge_document_not_found(
    knowledge_routes_with_mocks,
    fake_cursor,
):
    with pytest.raises(HTTPException) as exc_info:
        knowledge_routes_with_mocks.get_document(uuid4(), cursor=fake_cursor)

    assert exc_info.value.status_code == 404
    assert "Document not found" in exc_info.value.detail


def test_delete_knowledge_document(
    knowledge_routes_with_mocks,
    fake_cursor,
    test_store,
):
    from app.schemas.knowledge import KnowledgeDocumentCreate

    body = KnowledgeDocumentCreate(
        content="To be deleted",
        doc_type=KnowledgeType.PLAN,
        title="Delete Me",
    )
    create_response = knowledge_routes_with_mocks.create_document(body, cursor=fake_cursor)
    doc_id = create_response.document.document_id

    assert doc_id in test_store["knowledge"]

    knowledge_routes_with_mocks.delete_document(doc_id, cursor=fake_cursor)

    assert doc_id not in test_store["knowledge"]


def test_delete_knowledge_document_not_found(
    knowledge_routes_with_mocks,
    fake_cursor,
):
    with pytest.raises(HTTPException) as exc_info:
        knowledge_routes_with_mocks.delete_document(uuid4(), cursor=fake_cursor)

    assert exc_info.value.status_code == 404
    assert "Document not found" in exc_info.value.detail


def test_get_knowledge_documents_by_type(
    knowledge_routes_with_mocks,
    fake_cursor,
):
    from app.schemas.knowledge import KnowledgeDocumentCreate

    knowledge_routes_with_mocks.create_document(
        KnowledgeDocumentCreate(
            content="Plan content",
            doc_type=KnowledgeType.PLAN,
            title="Plan Doc",
        ),
        cursor=fake_cursor,
    )
    knowledge_routes_with_mocks.create_document(
        KnowledgeDocumentCreate(
            content="Code content",
            doc_type=KnowledgeType.CODE,
            title="Code Doc",
        ),
        cursor=fake_cursor,
    )

    response = knowledge_routes_with_mocks.get_documents(
        doc_type=KnowledgeType.PLAN,
        cursor=fake_cursor,
    )

    assert len(response.documents) == 1
    assert response.documents[0].doc_type == KnowledgeType.PLAN
    assert response.documents[0].content == "Plan content"


def test_get_knowledge_documents_by_type_empty(
    knowledge_routes_with_mocks,
    fake_cursor,
):
    response = knowledge_routes_with_mocks.get_documents(
        doc_type=KnowledgeType.CODE,
        cursor=fake_cursor,
    )

    assert response.documents == []
