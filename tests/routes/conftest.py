"""
Route-level fixtures.

Depends on root conftest for: test_store, fake_cursor, mock_repositories,
sample_user_request, sample_video_plan.
"""
from typing import Any

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# JOBS ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def jobs_routes_with_runner_mock(
    monkeypatch: pytest.MonkeyPatch,
    mock_repositories: None,
    test_store: dict[str, Any],
):
    """
    Returns the jobs routes module with:
    - All repository methods replaced by test_store equivalents (via mock_repositories).
    - WorkerRunner.advance replaced by a recorder that appends to test_store.
    """
    from app.routes import jobs as jobs_routes

    monkeypatch.setattr(
        jobs_routes.WorkerRunner,
        "advance",
        staticmethod(lambda job_request: test_store["worker_runner_calls"].append(job_request)),
    )
    return jobs_routes


# ─────────────────────────────────────────────────────────────────────────────
# ARTIFACTS ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_storage_service(test_store: dict[str, Any]):
    """
    In-memory MinIO replacement.
    Reads/writes objects to test_store["objects"] keyed by object_name.
    """
    from pathlib import Path

    class FakeFilesStorageService:
        def download_artifact(self, object_name: str, file_path: str) -> None:
            target = Path(file_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            data = test_store["objects"].get(object_name, b"fake-content")
            target.write_bytes(data)

        def delete_artifact(self, object_name: str) -> None:
            test_store["objects"].pop(object_name, None)

    return FakeFilesStorageService()


@pytest.fixture
def artifacts_routes_with_mocks(
    mock_repositories: None,
    mock_storage_service,
):
    """
    Returns the artifacts routes module with repository and storage mocked.
    mock_storage_service is injected directly into route calls via the
    `storage=` parameter.
    """
    from app.routes import artifacts as artifacts_routes

    return artifacts_routes


# ─────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_rag_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patches RAGService.embed_text to return a zero vector (avoids Ollama calls)."""
    import numpy as np
    from app.services import rag_service as rag_module

    monkeypatch.setattr(
        rag_module.RAGService,
        "embed_text",
        staticmethod(lambda text: np.zeros(768, dtype=np.float32)),
    )


@pytest.fixture
def mock_knowledge_repository(
    monkeypatch: pytest.MonkeyPatch,
    test_store: dict[str, Any],
) -> None:
    """Replaces KnowledgeRepository SQL methods with in-memory equivalents."""
    from app.repositories.knowledge_repository import KnowledgeRepository
    from app.schemas.knowledge import KnowledgeDocument, KnowledgeDocumentSchema, KnowledgeType

    S = KnowledgeDocumentSchema

    def create_document(_cursor, document_id, content, doc_type, title, embedding):
        test_store["knowledge"][document_id] = {
            S.DOCUMENT_ID.name: document_id,
            S.CONTENT.name: content,
            S.DOC_TYPE.name: doc_type,
            S.TITLE.name: title,
        }

    def get_document(_cursor, document_id):
        row = test_store["knowledge"].get(document_id)
        if row is None:
            return None
        return KnowledgeDocument(
            document_id=row[S.DOCUMENT_ID.name],
            content=row[S.CONTENT.name],
            doc_type=KnowledgeType(row[S.DOC_TYPE.name]),
            title=row[S.TITLE.name],
        )

    def delete_document(_cursor, document_id):
        return test_store["knowledge"].pop(document_id, None) is not None

    def get_documents(_cursor, doc_type):
        return [
            KnowledgeDocument(
                document_id=row[S.DOCUMENT_ID.name],
                content=row[S.CONTENT.name],
                doc_type=KnowledgeType(row[S.DOC_TYPE.name]),
                title=row[S.TITLE.name],
            )
            for row in test_store["knowledge"].values()
            if row[S.DOC_TYPE.name] == doc_type
        ]

    def search_similar(_cursor, embedding, doc_type, limit=3):
        return get_documents(None, doc_type)[:limit]

    def document_exists(_cursor, document_id):
        return document_id in test_store["knowledge"]

    monkeypatch.setattr(KnowledgeRepository, "create_document", staticmethod(create_document))
    monkeypatch.setattr(KnowledgeRepository, "get_document", staticmethod(get_document))
    monkeypatch.setattr(KnowledgeRepository, "get_documents", staticmethod(get_documents))
    monkeypatch.setattr(KnowledgeRepository, "delete_document", staticmethod(delete_document))
    monkeypatch.setattr(KnowledgeRepository, "search_similar", staticmethod(search_similar))
    monkeypatch.setattr(KnowledgeRepository, "document_exists", staticmethod(document_exists))


@pytest.fixture
def knowledge_routes_with_mocks(
    mock_knowledge_repository: None,
    mock_rag_service: None,
):
    """Returns the knowledge routes module with repository and RAG mocked."""
    from app.routes import knowledge as knowledge_routes

    return knowledge_routes


# ─────────────────────────────────────────────────────────────────────────────
# USAGE ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_token_ledger_repository(
    monkeypatch: pytest.MonkeyPatch,
    test_store: dict[str, Any],
) -> None:
    """
    Replaces TokenLedgerRepository.get_daily_summary with an in-memory
    aggregation over test_store["token_ledger"].
    """
    from datetime import date as date_type

    from app.configs.llm_settings import DAILY_TOKEN_LIMIT, SOFT_THRESHOLD_RATIO
    from app.repositories.token_repository import TokenLedgerRepository
    from app.schemas.token_usage import BreakdownEntry, DailySummary

    def get_daily_summary(_cursor, day: date_type):
        rows = [r for r in test_store["token_ledger"] if r["day"] == day]

        groups: dict[tuple, dict] = {}
        for row in rows:
            key = (row["provider"], row["model"], row["stage"])
            if key not in groups:
                groups[key] = {"consumed": 0, "reserved": 0}
            if row["state"] == "RELEASED":
                groups[key]["consumed"] += row["consumed_tokens"]
            if row["state"] == "ACTIVE":
                groups[key]["reserved"] += row["reserved_tokens"]

        breakdown = []
        total_consumed = total_reserved = 0
        for (provider, model, stage), totals in groups.items():
            breakdown.append(BreakdownEntry(
                provider=provider, model=model, stage=stage,
                consumed=totals["consumed"], reserved=totals["reserved"],
            ))
            total_consumed += totals["consumed"]
            total_reserved += totals["reserved"]

        used = total_consumed + total_reserved
        remaining = max(0, DAILY_TOKEN_LIMIT - used)
        remaining_pct = round((remaining / DAILY_TOKEN_LIMIT) * 100, 2) if DAILY_TOKEN_LIMIT > 0 else 0.0
        soft_threshold = int(DAILY_TOKEN_LIMIT * SOFT_THRESHOLD_RATIO)

        return DailySummary(
            daily_limit=DAILY_TOKEN_LIMIT,
            consumed=total_consumed,
            reserved=total_reserved,
            remaining=remaining,
            remaining_pct=remaining_pct,
            soft_threshold_exceeded=used >= soft_threshold,
            breakdown=breakdown,
        )

    monkeypatch.setattr(
        TokenLedgerRepository, "get_daily_summary", staticmethod(get_daily_summary)
    )


@pytest.fixture
def usage_routes_with_mocks(
    mock_token_ledger_repository: None,
):
    """Returns the usage routes module with the token ledger mocked."""
    from app.routes import usage as usage_routes

    return usage_routes
