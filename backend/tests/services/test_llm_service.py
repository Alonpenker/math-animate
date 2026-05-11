from contextlib import contextmanager

import pytest

from app.services.llm_service import LLMService

def test_extract_text_content_returns_string_content_directly():
    # Given
    class FakeResponse:
        content = "hello world"

    # When
    result = LLMService._extract_text_content(FakeResponse())

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
    result = LLMService._extract_text_content(FakeResponse())

    # Then
    assert result == "part one part two"

def test_extract_text_content_raises_value_error_for_unsupported_content_type():
    # Given
    class FakeResponse:
        content = 42  # unsupported

    # When / Then
    with pytest.raises(ValueError, match="non-text response"):
        LLMService._extract_text_content(FakeResponse())

def test_extract_text_content_raises_value_error_when_list_has_no_text_blocks():
    # Given
    class FakeResponse:
        content = [{"type": "image", "url": "http://example.com/img.png"}]

    # When / Then
    with pytest.raises(ValueError):
        LLMService._extract_text_content(FakeResponse())

def test_extract_token_usage_reads_values_from_usage_metadata():
    # Given
    class FakeResponse:
        usage_metadata = {
            "input_tokens": 100,
            "output_tokens": 50,
            "total_tokens": 150,
            "output_token_details": {"reasoning": 20},
        }

    # When
    input_tok, output_tok, total_tok, reasoning_tok = LLMService._extract_token_usage(FakeResponse())

    # Then
    assert input_tok == 100
    assert output_tok == 50
    assert total_tok == 150
    assert reasoning_tok == 20

def test_extract_token_usage_raises_runtime_error_when_no_usage_data_exists():
    # Given
    class FakeResponse:
        usage_metadata = None
        usage = None

    # When
    with pytest.raises(RuntimeError, match="Could not extract token usage"):
        LLMService._extract_token_usage(FakeResponse())

def test_extract_token_usage_returns_zeros_when_metadata_is_empty_dict():
    # Given
    class FakeResponse:
        usage_metadata = {}

    # When
    input_tok, output_tok, total_tok, reasoning_tok = LLMService._extract_token_usage(FakeResponse())

    # Then
    assert input_tok == 0
    assert output_tok == 0
    assert total_tok == 0
    assert reasoning_tok == 0

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

def test_render_plan_prompt_returns_static_system_prompt_and_user_request_string(
    monkeypatch: pytest.MonkeyPatch,
    sample_user_request,
):
    from app.configs.llm_settings import PLAN_SYSTEM_PROMPT
    # Given
    from app.services import llm_service as llm_module

    def boom_cursor():
        raise AssertionError("render_plan_prompt must not open a DB cursor")

    def boom_retrieve(*args, **kwargs):
        raise AssertionError("render_plan_prompt must not call SkillRetrievalService.retrieve")

    monkeypatch.setattr(llm_module, "get_worker_cursor", boom_cursor)
    monkeypatch.setattr(
        llm_module.SkillRetrievalService, "retrieve", staticmethod(boom_retrieve),
    )

    # When
    system_prompt, user_query = LLMService.render_plan_prompt(sample_user_request)

    # Then
    assert system_prompt == PLAN_SYSTEM_PROMPT
    assert user_query == str(sample_user_request)

def test_render_codegen_prompt_raises_when_core_documents_missing_skill_doc(
    monkeypatch: pytest.MonkeyPatch,
    sample_video_plan,
):
    # Given
    from app.services import llm_service as llm_module

    monkeypatch.setattr(llm_module, "CORE_DOCUMENTS", [])

    # When / Then
    with pytest.raises(ValueError, match="core skill document"):
        LLMService.render_codegen_prompt(sample_video_plan)

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
