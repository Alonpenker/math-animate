from uuid import uuid4

import pytest

from app.configs.llm_settings import (
    MAX_TOOL_LOADS, RAG_EXAMPLE_CAP, RAG_RULE_CAP, RAG_TEMPLATE_CAP,
)
from app.llm_knowledge.skill_documents import LLMKNOWLEDGE_DIR, REGISTRY
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
    )
    template_doc = KnowledgeDocument(
        document_id=uuid4(), doc_type=KnowledgeType.TEMPLATE, title="t1",
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

def _real_skill_seed() -> KnowledgeDocumentSeed:
    return next(s for s in REGISTRY if s.doc_type == KnowledgeType.SKILL)

def test_load_skill_document_returns_error_for_unknown_title():
    # Given
    candidates: dict[str, KnowledgeDocumentSeed] = {}
    tool = SkillRetrievalService.make_load_skill_document(candidates)

    # When
    result = tool.invoke({"title": "Nonexistent"})

    # Then
    assert "unknown or non-candidate" in result
    assert "Nonexistent" in result

def test_load_skill_document_returns_error_when_same_title_loaded_twice():
    # Given
    seed = _real_skill_seed()
    candidates = {seed.title: seed}
    tool = SkillRetrievalService.make_load_skill_document(candidates)

    # When
    first = tool.invoke({"title": seed.title})
    second = tool.invoke({"title": seed.title})

    # Then
    assert "already loaded" not in first
    assert len(first) > 0
    assert "already loaded" in second

def test_load_skill_document_returns_error_when_load_cap_reached(
    monkeypatch: pytest.MonkeyPatch,
):
    # Given
    monkeypatch.setattr(
        srs_module, "read_knowledge_file",
        lambda path: "fake content",
    )

    assert MAX_TOOL_LOADS == 8
    candidates: dict[str, KnowledgeDocumentSeed] = {}
    for i in range(MAX_TOOL_LOADS + 1):
        title = f"doc-{i}"
        candidates[title] = KnowledgeDocumentSeed(
            document_id=uuid4(),
            doc_type=KnowledgeType.SKILL,
            title=title,
            priority="core",
            path="manim_skill/SKILL.md",  # path is irrelevant — read_knowledge_file is mocked
        )

    tool = SkillRetrievalService.make_load_skill_document(candidates)

    # When
    results = [tool.invoke({"title": f"doc-{i}"}) for i in range(MAX_TOOL_LOADS)]
    overflow = tool.invoke({"title": f"doc-{MAX_TOOL_LOADS}"})

    # Then
    assert all(r == "fake content" for r in results)
    assert "skill document load limit reached" in overflow
    assert str(MAX_TOOL_LOADS) in overflow

def test_load_skill_document_returns_file_content_then_rejects_repeat():
    # Given
    seed = _real_skill_seed()
    expected_content = (LLMKNOWLEDGE_DIR / seed.path).read_text(encoding="utf-8")
    tool = SkillRetrievalService.make_load_skill_document({seed.title: seed})

    # When
    first = tool.invoke({"title": seed.title})
    second = tool.invoke({"title": seed.title})

    # Then
    assert first == expected_content
    assert "already loaded" in second
