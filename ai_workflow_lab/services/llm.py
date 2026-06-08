import json
import os
from dataclasses import dataclass
from typing import Protocol, TypeVar

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from pydantic import BaseModel

from schemas import CodePlan, CodeQaReport, VideoPlan
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


class LlmGateway(Protocol):
    def invoke(
        self,
        *,
        messages: list[BaseMessage],
        model: str,
        max_tokens: int | None = None,
        reasoning_effort: str | None = "high",
    ) -> tuple[BaseMessage, TokenUsage]:
        ...

    def invoke_structured(
        self,
        *,
        messages: list[BaseMessage],
        model: str,
        schema: type[StructuredModel],
        max_tokens: int | None = None,
        reasoning_effort: str | None = "high",
        request_timeout_ms: int | None = None,
    ) -> tuple[StructuredModel, TokenUsage]:
        ...


class RealLlmGateway:
    def invoke(
        self,
        *,
        messages: list[BaseMessage],
        model: str,
        max_tokens: int | None = None,
        reasoning_effort: str | None = "high",
    ) -> tuple[BaseMessage, TokenUsage]:
        client = self._get_client(
            model=model,
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort,
        )
        response = client.invoke(messages)
        return response, usage_from_response(response)

    def invoke_structured(
        self,
        *,
        messages: list[BaseMessage],
        model: str,
        schema: type[StructuredModel],
        max_tokens: int | None = None,
        reasoning_effort: str | None = "high",
        request_timeout_ms: int | None = None,
    ) -> tuple[StructuredModel, TokenUsage]:
        client = self._get_client(
            model=model,
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort,
            require_parameters=True,
            request_timeout_ms=request_timeout_ms,
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

    @staticmethod
    def _api_key() -> str:
        value = os.getenv("OPENROUTER_API_KEY")
        if not value:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. Export it or create ai_workflow_lab/.env."
            )
        return value

    def _get_client(
        self,
        *,
        model: str,
        max_tokens: int | None = None,
        reasoning_effort: str | None = "high",
        require_parameters: bool = False,
        request_timeout_ms: int | None = None,
    ):
        import openrouter
        from langchain_openrouter import ChatOpenRouter

        api_key = self._api_key()
        native_client = openrouter.OpenRouter(
            api_key=api_key,
            server_url=OPENROUTER_BASE_URL,
            http_referer=OPENROUTER_HTTP_REFERER,
            x_open_router_title=OPENROUTER_APP_TITLE,
            timeout_ms=request_timeout_ms,
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


class FakeE2ELlmGateway:
    def __init__(self) -> None:
        self._codegen_completed = False
        self._fix_completed = False

    def invoke(
        self,
        *,
        messages: list[BaseMessage],
        model: str,
        max_tokens: int | None = None,
        reasoning_effort: str | None = "high",
    ) -> tuple[BaseMessage, TokenUsage]:
        last_human_text = _last_human_text(messages)
        all_text = _all_message_text(messages)

        if last_human_text.startswith("Generate Manim code from these JSON contracts"):
            if self._codegen_completed:
                raise RuntimeError("E2E fake LLM received duplicate codegen call.")
            _require(
                "Video plan JSON:" in last_human_text and '"scenes"' in last_human_text,
                "E2E codegen prompt did not include video plan JSON.",
            )
            _require(
                "Code implementation plan JSON:" in last_human_text,
                "E2E codegen prompt did not include code implementation plan JSON.",
            )
            _require(
                "Visual Kit API" in all_text and "SafeScene" in all_text,
                "E2E codegen prompt did not include loaded visual-kit context.",
            )
            _require(
                "# Core Skill Documents" in all_text
                and "# Selected Skill Documents" in all_text,
                "E2E codegen call did not include loaded knowledge messages.",
            )
            self._codegen_completed = True
            content = _E2E_INVALID_CODE
        elif "verification failed" in last_human_text:
            _require(self._codegen_completed, "E2E fix call happened before codegen.")
            _require(not self._fix_completed, "E2E fake LLM received duplicate fix call.")
            _require(
                "Static verification failed:" in last_human_text
                and "Forbidden imports: os" in last_human_text,
                "E2E fix prompt did not include the expected verification failure.",
            )
            _require(
                _E2E_INVALID_CODE.strip() in all_text,
                "E2E fix call did not include the prior invalid assistant response.",
            )
            _require(
                "Return the complete corrected lesson body." in last_human_text,
                "E2E fix prompt did not include the complete-body instruction.",
            )
            _require(
                "Visual-kit API contract:" in all_text and "SafeScene" in all_text,
                "E2E fix prompt did not include the visual-kit API contract.",
            )
            self._fix_completed = True
            content = _E2E_FIXED_CODE
        else:
            raise RuntimeError("E2E fake LLM received an unexpected unstructured prompt.")

        return AIMessage(content=content), _zero_usage()

    def invoke_structured(
        self,
        *,
        messages: list[BaseMessage],
        model: str,
        schema: type[StructuredModel],
        max_tokens: int | None = None,
        reasoning_effort: str | None = "high",
        request_timeout_ms: int | None = None,
    ) -> tuple[StructuredModel, TokenUsage]:
        if schema is CodeQaReport:
            all_text = _all_message_text(messages)
            _require(
                "Line-numbered lesson-body Manim code:" in all_text,
                "E2E code QA prompt did not include line-numbered code.",
            )
            _require(
                "Code implementation plan JSON:" in all_text,
                "E2E code QA prompt did not include code implementation plan JSON.",
            )
            report_json = json.dumps({
                "decision": "pass",
                "summary": "E2E fake QA passes generated code.",
                "issues": [],
                "fix_instructions": "No QA fixes required.",
            })
            report = schema.model_validate_json(report_json)
            return report, _zero_usage()

        if schema is CodePlan:
            all_text = _all_message_text(messages)
            _require(
                "Teacher request:" in all_text and "Video plan JSON:" in all_text,
                "E2E code plan prompt did not include request and video plan.",
            )
            _require(
                "Required scene_number values:" in all_text,
                "E2E code plan prompt did not include required scene coverage.",
            )
            _require(
                "# Core Skill Documents" in all_text
                and "# Selected Skill Documents" in all_text,
                "E2E code plan call did not include loaded knowledge messages.",
            )
            code_plan_json = json.dumps({
                "scenes": [
                    {
                        "scene_number": 1,
                        "scene_title": "E2E workflow",
                        "subscenes": [
                            {
                                "id": "confirmation_start",
                                "purpose": "Show one clear confirmation line.",
                                "layout": "center",
                                "transition": "show",
                                "templates": [
                                    {
                                        "name": "status",
                                        "reference": "Equation Template",
                                        "parameters": {
                                            "state": "display",
                                            "expression": r"\text{Plan}\to\text{code}"
                                        },
                                    }
                                ],
                                "actions": [],
                                "caption": None,
                                "bottom_text": None,
                            },
                            {
                                "id": "confirmation_complete",
                                "purpose": "Reveal that rendering completed.",
                                "layout": "center",
                                "transition": "transform",
                                "templates": [
                                    {
                                        "name": "status",
                                        "reference": "Equation Template",
                                        "parameters": {
                                            "state": "display",
                                            "expression": (
                                                r"\text{Plan}\to\text{code}"
                                                r"\to\text{verify}"
                                            )
                                        },
                                    }
                                ],
                                "actions": [
                                    {
                                        "target": "status",
                                        "action": "set_expression",
                                        "parameters": {
                                            "expression": (
                                                r"\text{Plan}\to\text{code}"
                                                r"\to\text{verify}\to\text{render}"
                                            )
                                        },
                                    }
                                ],
                                "caption": None,
                                "bottom_text": "The local workflow reached the visual-kit render path.",
                            },
                        ],
                    }
                ],
            })
            code_plan = schema.model_validate_json(code_plan_json)
            return code_plan, _zero_usage()

        if schema is not VideoPlan:
            raise RuntimeError(f"E2E fake LLM does not support schema {schema.__name__}.")
        request_text = _last_human_text(messages)
        _require(request_text, "E2E planner call did not include a human request.")
        request_excerpt = " ".join(request_text.split())[:120]
        plan_json = json.dumps({
            "scenes": [
                {
                    "scene_number": 1,
                    "learning_objective": (
                        "Confirm the lab workflow can plan, fix, verify, and render one scene "
                        f"for this request: {request_excerpt}"
                    ),
                    "visual_storyboard": (
                        "Show a centered title, then a small green confirmation line below it. "
                        "End with the green confirmation visible."
                    ),
                    "voice_notes": "This local end-to-end run verifies the workflow without real API calls.",
                }
            ]
        })
        plan = schema.model_validate_json(plan_json)
        return plan, _zero_usage()


def create_llm_gateway(*, e2e: bool) -> LlmGateway:
    if e2e:
        return FakeE2ELlmGateway()
    return RealLlmGateway()


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


def _zero_usage() -> TokenUsage:
    return TokenUsage()


def _last_human_text(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return _message_text(message)
    return ""


def _all_message_text(messages: list[BaseMessage]) -> str:
    return "\n\n".join(_message_text(message) for message in messages)


def _message_text(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block["text"]
            for block in content
            if isinstance(block, dict)
            and block.get("type") == "text"
            and isinstance(block.get("text"), str)
        )
    return str(content)


def _require(condition: object, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


_E2E_INVALID_CODE = """from manim import *
import os


class Scene1(Scene):
    def construct(self):
        self.add(Text("This first E2E code intentionally fails static verification."))
"""


_E2E_FIXED_CODE = """from manim import *


class Scene1(SafeScene):
    def construct(self):
        self.show_title("E2E workflow")
        self._subscene_confirmation_start()
        self._subscene_confirmation_complete()
        self.fade_out_all()

    def _subscene_confirmation_start(self):
        self.clear_content()
        status = EquationTemplate.build(
            state="display",
            expression=r"\\text{Plan}\\to\\text{code}",
        )
        self.show_main(status, layout=Layout.CENTER)
        self.set_bottom_text(None)
        self.wait(0.25)

    def _subscene_confirmation_complete(self):
        status = EquationTemplate.build(
            state="display",
            expression=r"\\text{Plan}\\to\\text{code}\\to\\text{verify}"
        )
        self.transform_main(status, layout=Layout.CENTER)
        self.play_action(status.set_expression(
            expression=r"\\text{Plan}\\to\\text{code}\\to\\text{verify}\\to\\text{render}"
        ))
        self.set_bottom_text("The local workflow reached the visual-kit render path.")
        self.wait(0.5)
"""
