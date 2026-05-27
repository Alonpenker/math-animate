from typing import Any

import pytest

from app.dependencies.limiter import limiter as _limiter
_limiter.limit = lambda *args, **kwargs: (lambda f: f)

@pytest.fixture
def jobs_routes_with_runner_mock(
    monkeypatch: pytest.MonkeyPatch,
    mock_repositories: None,
    test_store: dict[str, Any],
):
    from app.routes import jobs as jobs_routes

    monkeypatch.setattr(
        jobs_routes.WorkerRunner,
        "advance",
        staticmethod(lambda job_request: test_store["worker_runner_calls"].append(job_request)),
    )
    return jobs_routes

@pytest.fixture
def mock_storage_service(test_store: dict[str, Any]):
    from io import BytesIO
    from pathlib import Path

    class FakeObjectStream(BytesIO):
        def release_conn(self) -> None:
            pass

    class FakeFilesStorageService:
        def download_artifact(self, object_name: str, file_path: str) -> None:
            target = Path(file_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            data = test_store["objects"].get(object_name, b"fake-content")
            target.write_bytes(data)

        def delete_artifact(self, object_name: str) -> None:
            test_store["objects"].pop(object_name, None)

        def get_artifact_size(self, object_name: str) -> int:
            data = test_store["objects"].get(object_name, b"fake-content")
            return len(data)

        def open_artifact_stream(
            self,
            object_name: str,
            offset: int = 0,
            length: int = 0,
        ) -> FakeObjectStream:
            data = test_store["objects"].get(object_name, b"fake-content")
            sliced = data[offset:]
            if length > 0:
                sliced = sliced[:length]
            return FakeObjectStream(sliced)

    return FakeFilesStorageService()

@pytest.fixture
def artifacts_routes_with_mocks(
    mock_repositories: None,
    mock_storage_service,
):
    from app.routes import artifacts as artifacts_routes

    return artifacts_routes

@pytest.fixture
def mock_rag_service(monkeypatch: pytest.MonkeyPatch) -> None:
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
    from app.repositories.knowledge_repository import KnowledgeRepository
    from app.schemas.knowledge import KnowledgeDocument, KnowledgeDocumentSchema, KnowledgeType

    S = KnowledgeDocumentSchema

    def create_document(_cursor, *, document_id, doc_type, title, embedding,
                        category, priority="optional", tags=None):
        test_store["knowledge"][document_id] = {
            S.DOCUMENT_ID.name: document_id,
            S.DOC_TYPE.name: doc_type,
            S.TITLE.name: title,
            S.CATEGORY.name: category,
            S.PRIORITY.name: priority,
            S.TAGS.name: tags or [],
        }

    def get_document(_cursor, document_id):
        row = test_store["knowledge"].get(document_id)
        if row is None:
            return None
        return KnowledgeDocument(
            document_id=row[S.DOCUMENT_ID.name],
            doc_type=KnowledgeType(row[S.DOC_TYPE.name]),
            title=row[S.TITLE.name],
            category=row[S.CATEGORY.name],
            priority=row[S.PRIORITY.name],
            tags=row[S.TAGS.name] or [],
        )

    def delete_document(_cursor, document_id):
        return test_store["knowledge"].pop(document_id, None) is not None

    def get_documents(_cursor, doc_type):
        return [
            KnowledgeDocument(
                document_id=row[S.DOCUMENT_ID.name],
                doc_type=KnowledgeType(row[S.DOC_TYPE.name]),
                title=row[S.TITLE.name],
                category=row[S.CATEGORY.name],
                priority=row[S.PRIORITY.name],
                tags=row[S.TAGS.name] or [],
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
    monkeypatch: pytest.MonkeyPatch,
    mock_knowledge_repository: None,
    mock_rag_service: None,
    test_store: dict[str, Any],
):
    from app.routes import knowledge as knowledge_routes

    monkeypatch.setattr(
        knowledge_routes.WorkerRunner,
        "handle_seed",
        staticmethod(lambda: test_store["worker_runner_calls"].append({"op": "seed"})),
    )

    return knowledge_routes

@pytest.fixture
def mock_token_ledger_repository(
    monkeypatch: pytest.MonkeyPatch,
    test_store: dict[str, Any],
) -> None:
    from datetime import date as date_type

    from app.configs.llm_settings import LLM_PROVIDER, OPENROUTER_DAILY_CALL_LIMIT
    from app.repositories.token_repository import TokenLedgerRepository
    from app.schemas.token_usage import BreakdownEntry, DailySummary, TokenTotals

    def get_daily_summary(_cursor, day: date_type):
        rows = [
            r for r in test_store["token_ledger"]
            if r["day"] == day and r["provider"] == LLM_PROVIDER.OPENROUTER.value
        ]

        groups: dict[tuple, dict] = {}
        for row in rows:
            key = (row["provider"], row["model"], row["stage"], row.get("call_type", "unknown"))
            if key not in groups:
                groups[key] = {
                    "calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "reasoning_tokens": 0,
                    "total_tokens": 0,
                }
            groups[key]["calls"] += 1
            groups[key]["input_tokens"] += row.get("input_tokens", 0)
            groups[key]["output_tokens"] += row.get("output_tokens", 0)
            groups[key]["reasoning_tokens"] += row.get("reasoning_tokens", 0)
            groups[key]["total_tokens"] += row.get("consumed_tokens", 0)

        breakdown = []
        calls = input_tokens = output_tokens = reasoning_tokens = total_tokens = 0
        for (provider, model, stage, call_type), totals in groups.items():
            breakdown.append(BreakdownEntry(
                provider=provider,
                model=model,
                stage=stage,
                call_type=call_type,
                calls=totals["calls"],
                input_tokens=totals["input_tokens"],
                output_tokens=totals["output_tokens"],
                reasoning_tokens=totals["reasoning_tokens"],
                total_tokens=totals["total_tokens"],
            ))
            calls += totals["calls"]
            input_tokens += totals["input_tokens"]
            output_tokens += totals["output_tokens"]
            reasoning_tokens += totals["reasoning_tokens"]
            total_tokens += totals["total_tokens"]

        return DailySummary(
            openrouter_calls=calls,
            openrouter_call_limit=OPENROUTER_DAILY_CALL_LIMIT,
            openrouter_calls_remaining=max(0, OPENROUTER_DAILY_CALL_LIMIT - calls),
            token_totals=TokenTotals(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                reasoning_tokens=reasoning_tokens,
                total_tokens=total_tokens,
            ),
            breakdown=breakdown,
        )

    monkeypatch.setattr(
        TokenLedgerRepository, "get_daily_summary", staticmethod(get_daily_summary)
    )

@pytest.fixture
def usage_routes_with_mocks(
    mock_token_ledger_repository: None,
):
    from app.routes import usage as usage_routes

    return usage_routes
