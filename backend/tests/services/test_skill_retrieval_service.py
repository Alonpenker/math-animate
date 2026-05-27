from uuid import uuid4

import pytest

from app.configs.llm_settings import (
    RAG_EXAMPLE_CAP, RAG_RULE_CAP, RAG_TEMPLATE_CAP,
)
from app.llm_knowledge.skill_documents import LLMKNOWLEDGE_DIR, REGISTRY
from app.llm_knowledge.categories import RuleCategory, TemplateCategory
from app.schemas.knowledge import (
    CandidateResult, KnowledgeDocumentSeed, KnowledgeType,
)
from app.services import skill_retrieval_service as srs_module
from app.services.skill_retrieval_service import SkillRetrievalService


def test_retrieve_calls_search_similar_with_correct_caps_per_doc_type(
    monkeypatch: pytest.MonkeyPatch,
):
    # Given
    import numpy as np

    monkeypatch.setattr(
        srs_module.RAGService,
        "embed_text",
        staticmethod(lambda text: np.zeros(8, dtype=np.float32)),
    )

    calls: list[tuple] = []

    def fake_search_similar(cursor, embedding, doc_type, limit):
        calls.append((doc_type, limit))
        return []

    monkeypatch.setattr(
        srs_module.KnowledgeRepository,
        "search_similar",
        staticmethod(fake_search_similar),
    )

    # When
    result = SkillRetrievalService.retrieve(cursor=object(), plan_text="some plan")

    # Then
    assert isinstance(result, CandidateResult)
    assert result.candidate_rules == []
    assert result.candidate_templates == []
    assert result.candidate_examples == []

    assert calls == [
        (KnowledgeType.RULE.value, RAG_RULE_CAP),
        (KnowledgeType.TEMPLATE.value, RAG_TEMPLATE_CAP),
        (KnowledgeType.EXAMPLE.value, RAG_EXAMPLE_CAP),
    ]


def test_retrieve_returns_candidate_result_with_search_results(
    monkeypatch: pytest.MonkeyPatch,
):
    # Given
    import numpy as np

    from app.schemas.knowledge import KnowledgeDocument

    rule_doc = KnowledgeDocument(
        document_id=uuid4(), doc_type=KnowledgeType.RULE, title="r1",
        category=RuleCategory.GENERAL,
    )
    template_doc = KnowledgeDocument(
        document_id=uuid4(), doc_type=KnowledgeType.TEMPLATE, title="t1",
        category=TemplateCategory.TEMPLATES,
    )

    monkeypatch.setattr(
        srs_module.RAGService,
        "embed_text",
        staticmethod(lambda text: np.zeros(8, dtype=np.float32)),
    )

    def fake_search_similar(cursor, embedding, doc_type, limit):
        if doc_type == KnowledgeType.RULE.value:
            return [rule_doc]
        if doc_type == KnowledgeType.TEMPLATE.value:
            return [template_doc]
        return []

    monkeypatch.setattr(
        srs_module.KnowledgeRepository,
        "search_similar",
        staticmethod(fake_search_similar),
    )

    # When
    result = SkillRetrievalService.retrieve(cursor=object(), plan_text="plan")

    # Then
    assert result.candidate_rules == [rule_doc]
    assert result.candidate_templates == [template_doc]
    assert result.candidate_examples == []
    assert result.all_candidates == [rule_doc, template_doc]


def test_retrieve_excludes_core_documents(
    monkeypatch: pytest.MonkeyPatch,
):
    """Core documents must never appear in the candidate list — they are injected separately."""
    import numpy as np
    from app.llm_knowledge.skill_documents import CORE_DOCUMENTS
    from app.schemas.knowledge import KnowledgeDocument

    core_doc = KnowledgeDocument(
        document_id=CORE_DOCUMENTS[0].document_id,
        doc_type=KnowledgeType.RULE,
        title="Core Rule",
        category=RuleCategory.GENERAL,
    )
    non_core_doc = KnowledgeDocument(
        document_id=uuid4(), doc_type=KnowledgeType.RULE, title="Non-Core Rule",
        category=RuleCategory.GENERAL,
    )

    monkeypatch.setattr(
        srs_module.RAGService,
        "embed_text",
        staticmethod(lambda text: np.zeros(8, dtype=np.float32)),
    )

    def fake_search_similar(cursor, embedding, doc_type, limit):
        if doc_type == KnowledgeType.RULE.value:
            return [core_doc, non_core_doc]
        return []

    monkeypatch.setattr(
        srs_module.KnowledgeRepository,
        "search_similar",
        staticmethod(fake_search_similar),
    )

    # When
    result = SkillRetrievalService.retrieve(cursor=object(), plan_text="plan")

    # Then — core doc is excluded, non-core doc is present
    assert core_doc not in result.candidate_rules
    assert non_core_doc in result.candidate_rules
