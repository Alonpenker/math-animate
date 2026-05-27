from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.llm_knowledge.categories import RuleCategory, TemplateCategory
from app.routes import knowledge as knowledge_routes
from app.schemas.knowledge import KnowledgeDocumentSchema, KnowledgeType

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
        S.DOC_TYPE.name: KnowledgeType.RULE.value,
        S.TITLE.name: "Test Rule",
        S.CATEGORY.name: RuleCategory.GENERAL.value,
        S.PRIORITY.name: "recommended",
        S.TAGS.name: ["foo"],
    }

    # When
    response = knowledge_routes_with_mocks.get_document(
        request=object(), document_id=doc_id, cursor=fake_cursor
    )

    # Then
    assert response.document.document_id == doc_id
    assert response.document.title == "Test Rule"
    assert response.document.doc_type == KnowledgeType.RULE
    assert response.document.category == RuleCategory.GENERAL
    assert response.document.priority == "recommended"
    assert response.document.tags == ["foo"]

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

def test_get_documents_by_type_returns_only_matching_type(
    knowledge_routes_with_mocks,
    fake_cursor,
    test_store,
):
    # Given — seed knowledge store directly
    S = KnowledgeDocumentSchema
    rule_id = uuid4()
    template_id = uuid4()
    test_store["knowledge"][rule_id] = {
        S.DOCUMENT_ID.name: rule_id,
        S.DOC_TYPE.name: KnowledgeType.RULE.value,
        S.TITLE.name: "Rule Doc",
        S.CATEGORY.name: RuleCategory.GENERAL.value,
        S.PRIORITY.name: "recommended",
        S.TAGS.name: [],
    }
    test_store["knowledge"][template_id] = {
        S.DOCUMENT_ID.name: template_id,
        S.DOC_TYPE.name: KnowledgeType.TEMPLATE.value,
        S.TITLE.name: "Template Doc",
        S.CATEGORY.name: TemplateCategory.TEMPLATES.value,
        S.PRIORITY.name: "recommended",
        S.TAGS.name: [],
    }

    # When
    response = knowledge_routes_with_mocks.get_documents(
        request=object(), doc_type=KnowledgeType.RULE, cursor=fake_cursor
    )

    # Then
    assert len(response.documents) == 1
    assert response.documents[0].doc_type == KnowledgeType.RULE
    assert response.documents[0].title == "Rule Doc"

def test_get_documents_by_type_returns_empty_list_when_none_of_that_type_exist(
    knowledge_routes_with_mocks,
    fake_cursor,
):

    # Given — empty knowledge store
    # When
    response = knowledge_routes_with_mocks.get_documents(
        request=object(), doc_type=KnowledgeType.RULE, cursor=fake_cursor
    )

    # Then
    assert response.documents == []
