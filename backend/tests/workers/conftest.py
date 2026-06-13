from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

@pytest.fixture
def mock_worker_cursor(monkeypatch: pytest.MonkeyPatch, fake_cursor: object) -> None:
    from app.workers import worker as worker_module
    from app.workers import worker_helpers
    from app.services import openrouter_service

    @contextmanager
    def fake_cursor_ctx():
        yield fake_cursor

    @contextmanager
    def fake_redis_ctx():
        yield object()  # ignored — JobsRepository methods are patched

    monkeypatch.setattr(worker_module, "get_worker_cursor", fake_cursor_ctx)
    monkeypatch.setattr(worker_helpers, "get_worker_cursor", fake_cursor_ctx)
    monkeypatch.setattr(openrouter_service, "get_worker_cursor", fake_cursor_ctx)
    monkeypatch.setattr(worker_helpers, "get_worker_redis", fake_redis_ctx)

@pytest.fixture
def mock_worker_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    from app.workers import worker as worker_module

    artifacts_root = tmp_path / "job_artifacts"
    render_root = tmp_path / "render_root"
    artifacts_root.mkdir(parents=True, exist_ok=True)
    render_root.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(worker_module.PathNames, "ARTIFACTS_FOLDER", str(artifacts_root))
    monkeypatch.setattr(worker_module.PathNames, "TMP_RENDER_FOLDER", str(render_root))
    return {"artifacts_root": artifacts_root, "render_root": render_root}

@pytest.fixture
def mock_worker_storage(monkeypatch: pytest.MonkeyPatch, test_store: dict[str, Any]) -> None:
    from app.workers import worker_helpers

    class FakeStorageService:
        def __init__(self, client: Any = None, bucket: str = "") -> None:
            pass

        def save_artifact(self, job_id, file_path: Path) -> str:
            path = Path(file_path)
            object_name = f"{job_id}/{path.name}"
            test_store["objects"][object_name] = path.read_bytes()
            return object_name

        def download_artifact(self, object_name: str, file_path: str) -> None:
            target = Path(file_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(test_store["objects"][object_name])

    monkeypatch.setattr(worker_helpers, "FilesStorageService", FakeStorageService)
    monkeypatch.setattr(worker_helpers, "get_storage_client", lambda: object())

@pytest.fixture
def mock_worker_llm(monkeypatch: pytest.MonkeyPatch, sample_video_plan) -> None:
    from app.workers import worker as worker_module

    fake_code = (
        "from manim import *\n\n"
        "class Scene1(Scene):\n"
        "    def construct(self):\n"
        "        self.wait()\n"
    )

    monkeypatch.setattr(
        worker_module.LLMService, "render_plan_prompt",
        staticmethod(lambda user_request: ("fake-system-prompt", "fake-user-query")),
    )
    monkeypatch.setattr(
        worker_module.LLMService, "render_codegen_prompt",
        staticmethod(lambda plan: ("fake-system-prompt", "fake-user-query", [])),
    )
    monkeypatch.setattr(
        worker_module.LLMService, "plan_call",
        staticmethod(lambda system_prompt, user_query: (sample_video_plan, 100)),
    )
    monkeypatch.setattr(
        worker_module.LLMService, "codegen_call",
        staticmethod(lambda system_prompt, user_query, tools=None: (fake_code, 200)),
    )

@pytest.fixture
def mock_worker_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.workers import worker_helpers

    monkeypatch.setattr(
        worker_helpers.BudgetService, "reserve",
        staticmethod(lambda cursor, call_id, job_id, stage, provider, model, prompt_text: 1000),
    )
    monkeypatch.setattr(
        worker_helpers.BudgetService, "reconcile",
        staticmethod(lambda cursor, call_id, consumed_tokens: None),
    )
    monkeypatch.setattr(
        worker_helpers.BudgetService, "release_on_error",
        staticmethod(lambda cursor, call_id, reserved_tokens: None),
    )

@pytest.fixture
def capture_render_delay(monkeypatch: pytest.MonkeyPatch, test_store: dict[str, Any]) -> None:
    from app.workers import worker as worker_module

    monkeypatch.setattr(
        worker_module.generate_render,
        "delay",
        lambda payload: test_store["render_delay_payloads"].append(payload),
    )
