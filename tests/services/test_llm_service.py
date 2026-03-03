"""
LLMService tests.

Focuses on testable pure/static methods and E2E stub paths.
Methods that make real LangChain/OpenAI API calls are NOT tested here — those
require integration test infrastructure (real API key, network).
"""
from contextlib import contextmanager

import pytest

from app.services.llm_service import LLMService


# ─────────────────────────────────────────────────────────────────────────────
# LLMService.extract_text_content
# ─────────────────────────────────────────────────────────────────────────────

def test_extract_text_content_returns_string_content_directly():
    # Given
    class FakeResponse:
        content = "hello world"

    # When
    result = LLMService.extract_text_content(FakeResponse())

    # Then
    assert result == "hello world"


def test_extract_text_content_joins_text_blocks_from_list_content():
    # Given
    class FakeResponse:
        content = [
            {"type": "text", "text": "part one"},
            {"type": "text", "text": " part two"},
        ]

    # When
    result = LLMService.extract_text_content(FakeResponse())

    # Then
    assert result == "part one part two"


def test_extract_text_content_raises_value_error_for_unsupported_content_type():
    # Given
    class FakeResponse:
        content = 42  # unsupported

    # When / Then
    with pytest.raises(ValueError, match="non-text response"):
        LLMService.extract_text_content(FakeResponse())


def test_extract_text_content_raises_value_error_when_list_has_no_text_blocks():
    # Given
    class FakeResponse:
        content = [{"type": "image", "url": "http://example.com/img.png"}]

    # When / Then
    with pytest.raises(ValueError):
        LLMService.extract_text_content(FakeResponse())


# ─────────────────────────────────────────────────────────────────────────────
# LLMService._extract_token_usage
# ─────────────────────────────────────────────────────────────────────────────

def test_extract_token_usage_reads_values_from_usage_metadata():
    # Given
    class FakeResponse:
        usage_metadata = {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150}

    # When
    input_tok, output_tok, total_tok = LLMService._extract_token_usage(FakeResponse())

    # Then
    assert input_tok == 100
    assert output_tok == 50
    assert total_tok == 150


def test_extract_token_usage_returns_zeros_when_no_metadata():
    # Given
    class FakeResponse:
        usage_metadata = None

    # When
    input_tok, output_tok, total_tok = LLMService._extract_token_usage(FakeResponse())

    # Then
    assert input_tok == 0
    assert output_tok == 0
    assert total_tok == 0


def test_extract_token_usage_returns_zeros_when_metadata_is_empty_dict():
    # Given
    class FakeResponse:
        usage_metadata = {}

    # When
    input_tok, output_tok, total_tok = LLMService._extract_token_usage(FakeResponse())

    # Then
    assert input_tok == 0
    assert output_tok == 0
    assert total_tok == 0


# ─────────────────────────────────────────────────────────────────────────────
# LLMService.render_fix_prompt
# ─────────────────────────────────────────────────────────────────────────────

def test_render_fix_prompt_includes_code_and_error_in_user_query():
    # Given
    code = "from manim import *\nclass Scene1(Scene): pass"
    error = "IndexError: list index out of range"

    # When
    system_prompt, user_query = LLMService.render_fix_prompt(code, error)

    # Then
    assert code in user_query
    assert error in user_query


def test_render_fix_prompt_uses_codegen_fix_system_prompt():
    # Given
    from app.configs.llm_settings import CODEGEN_FIX_SYSTEM_PROMPT

    # When
    system_prompt, _ = LLMService.render_fix_prompt("code", "error")

    # Then
    assert system_prompt == CODEGEN_FIX_SYSTEM_PROMPT


# ─────────────────────────────────────────────────────────────────────────────
# LLMService.render_plan_prompt
# ─────────────────────────────────────────────────────────────────────────────

def test_render_plan_prompt_injects_rag_examples_into_system_prompt(
    monkeypatch: pytest.MonkeyPatch,
    sample_user_request,
):
    # Given
    from app.services import llm_service as llm_module

    @contextmanager
    def fake_cursor_ctx():
        yield object()

    monkeypatch.setattr(llm_module, "get_worker_cursor", fake_cursor_ctx)
    monkeypatch.setattr(
        llm_module.LLMService, "retrieve_examples",
        staticmethod(lambda cursor, query, doc_type: "example plan content"),
    )

    # When
    system_prompt, user_query = LLMService.render_plan_prompt(sample_user_request)

    # Then
    assert "example plan content" in system_prompt
    assert sample_user_request.topic in user_query


def test_render_plan_prompt_includes_all_user_request_fields_in_query(
    monkeypatch: pytest.MonkeyPatch,
    sample_user_request,
):
    # Given
    from app.services import llm_service as llm_module

    @contextmanager
    def fake_cursor_ctx():
        yield object()

    monkeypatch.setattr(llm_module, "get_worker_cursor", fake_cursor_ctx)
    monkeypatch.setattr(
        llm_module.LLMService, "retrieve_examples",
        staticmethod(lambda cursor, query, doc_type: "(No examples available.)"),
    )

    # When
    _, user_query = LLMService.render_plan_prompt(sample_user_request)

    # Then
    assert sample_user_request.topic in user_query
    assert str(sample_user_request.number_of_scenes) in user_query


# ─────────────────────────────────────────────────────────────────────────────
# LLMService.plan_call / codegen_call / fix_call (E2E stub paths)
# ─────────────────────────────────────────────────────────────────────────────

def test_plan_call_returns_stub_plan_in_e2e_mode(monkeypatch: pytest.MonkeyPatch):
    # Given
    from app.services import llm_service as llm_module
    from app.schemas.video_plan import VideoPlan

    monkeypatch.setattr(llm_module, "IS_E2E_MODE", True)

    # When
    plan, total_tokens = LLMService.plan_call("system", "user")

    # Then
    assert isinstance(plan, VideoPlan)
    assert total_tokens == 0


def test_codegen_call_returns_stub_code_in_e2e_mode(monkeypatch: pytest.MonkeyPatch):
    # Given
    from app.services import llm_service as llm_module

    monkeypatch.setattr(llm_module, "IS_E2E_MODE", True)

    # When
    code, total_tokens = LLMService.codegen_call("system", "user")

    # Then
    assert isinstance(code, str)
    assert len(code) > 0
    assert total_tokens == 0


def test_fix_call_returns_stub_fixed_code_in_e2e_mode(monkeypatch: pytest.MonkeyPatch):
    # Given
    from app.services import llm_service as llm_module

    monkeypatch.setattr(llm_module, "IS_E2E_MODE", True)

    # When
    code, total_tokens = LLMService.fix_call("system", "user")

    # Then
    assert isinstance(code, str)
    assert len(code) > 0
    assert total_tokens == 0
