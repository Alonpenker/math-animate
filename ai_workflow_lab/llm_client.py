import os
from dataclasses import dataclass
from typing import TypeVar

import openrouter
from langchain_core.messages import BaseMessage
from langchain_openrouter import ChatOpenRouter
from pydantic import BaseModel

from settings import (
    OPENROUTER_APP_TITLE,
    OPENROUTER_BASE_URL,
    OPENROUTER_HTTP_REFERER,
)


StructuredModel = TypeVar("StructuredModel", bound=BaseModel)


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0


def _api_key() -> str:
    value = os.getenv("OPENROUTER_API_KEY")
    if not value:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Export it or create ai_workflow_lab/.env."
        )
    return value


def get_client(
    *,
    model: str,
    max_tokens: int | None = None,
    reasoning_effort: str | None = "high",
    require_parameters: bool = False,
) -> ChatOpenRouter:
    api_key = _api_key()
    native_client = openrouter.OpenRouter(
        api_key=api_key,
        server_url=OPENROUTER_BASE_URL,
        http_referer=OPENROUTER_HTTP_REFERER,
        x_open_router_title=OPENROUTER_APP_TITLE,
    )
    kwargs = {
        "model": model,
        "api_key": api_key,
        "client": native_client,
        "app_url": None,
        "app_title": None,
        "max_tokens": max_tokens,
    }
    if reasoning_effort is not None:
        kwargs["reasoning"] = {"effort": reasoning_effort}
    if require_parameters:
        kwargs["openrouter_provider"] = {"require_parameters": True}
    return ChatOpenRouter(**kwargs)


def usage_from_response(response: object) -> TokenUsage:
    usage_metadata = getattr(response, "usage_metadata", None) or {}
    input_tokens = int(usage_metadata.get("input_tokens", 0) or 0)
    output_tokens = int(usage_metadata.get("output_tokens", 0) or 0)
    total_tokens = int(usage_metadata.get("total_tokens", 0) or 0)
    output_details = usage_metadata.get("output_token_details", {}) or {}
    reasoning_tokens = int(output_details.get("reasoning") or 0)
    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        reasoning_tokens=reasoning_tokens,
        total_tokens=total_tokens or input_tokens + output_tokens,
    )


def invoke(
    *,
    messages: list[BaseMessage],
    model: str,
    max_tokens: int | None = None,
    reasoning_effort: str | None = "high",
) -> tuple[BaseMessage, TokenUsage]:
    client = get_client(
        model=model,
        max_tokens=max_tokens,
        reasoning_effort=reasoning_effort,
    )
    response = client.invoke(messages)
    return response, usage_from_response(response)


def invoke_structured(
    *,
    messages: list[BaseMessage],
    model: str,
    schema: type[StructuredModel],
    max_tokens: int | None = None,
) -> tuple[StructuredModel, TokenUsage]:
    client = get_client(
        model=model,
        max_tokens=max_tokens,
        reasoning_effort=None,
        require_parameters=True,
    )
    structured_client = client.with_structured_output(
        schema,
        method="json_schema",
        strict=True,
        include_raw=True,
    )
    result = structured_client.invoke(messages)

    raw_response = result.get("raw") if isinstance(result, dict) else result
    usage = usage_from_response(raw_response)
    parsed = result.get("parsed") if isinstance(result, dict) else result
    parsing_error = result.get("parsing_error") if isinstance(result, dict) else None

    if isinstance(parsed, schema):
        return parsed, usage

    content = getattr(raw_response, "content", None)
    if isinstance(content, str) and content.strip():
        try:
            return schema.model_validate_json(content), usage
        except Exception as exc:
            parsing_error = parsing_error or exc

    raise RuntimeError(
        f"Structured LLM response did not match {schema.__name__}. "
        f"parsed_type={type(parsed).__name__}, parsing_error={parsing_error}"
    )

