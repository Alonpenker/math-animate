import time
from enum import StrEnum

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from openai import LengthFinishReasonError
from pydantic import BaseModel, Field

from app.configs.app_settings import settings
from app.configs.llm_settings import (
    LLM_PLAN_MODEL, LLM_CODE_MODEL, LLM_TEMPERATURE,
    LLM_PLAN_OUTPUT_MAX_TOKENS, LLM_CODEGEN_OUTPUT_MAX_TOKENS,
    LLM_REASONING_EFFORT,
    PLAN_SYSTEM_PROMPT, CODEGEN_SYSTEM_PROMPT, CODEGEN_FIX_SYSTEM_PROMPT,
    MAX_TOOL_CALL_ITERATIONS,
)
from app.dependencies.db import get_worker_cursor
from app.exceptions.llm_usage_exception import LLMUsageException
from app.llm_knowledge.skill_documents import CORE_DOCUMENTS, REGISTRY_BY_ID, read_knowledge_file
from app.schemas.knowledge import KnowledgeType
from app.schemas.user_request import UserRequest
from app.schemas.video_plan import VideoPlan
from app.services.skill_retrieval_service import SkillRetrievalService
from app.utils.llm_stubs import IS_E2E_MODE, STUB_PLAN, STUB_BROKEN_CODE, STUB_FIXED_CODE
from app.utils.logging import Logger, WorkerLog, WorkerOperation

logger = Logger.get_logger("worker")

class CallType(StrEnum):
    PLAN = "plan"
    CODEGEN = "codegen"
    DOCUMENT_SELECTION = "document_selection"
    FIX = "fix"

class CodegenToolUsage(BaseModel):
    available_optional_titles: list[str] = Field(default_factory=list)
    model_iterations: int = 0
    tool_call_iterations: int = 0
    total_requested_tool_calls: int = 0
    requested_titles: list[str] = Field(default_factory=list)
    loaded_titles: list[str] = Field(default_factory=list)
    successful_optional_load_count: int = 0
    unknown_or_non_candidate_count: int = 0
    duplicate_count: int = 0
    load_limit_count: int = 0
    tool_execution_error_count: int = 0

class LLMService:

    _plan_model: ChatOpenAI | None = None
    _codegen_model: ChatOpenAI | None = None

    @classmethod
    def _get_plan_model(cls) -> ChatOpenAI:
        if cls._plan_model is None:
            cls._plan_model = ChatOpenAI(
                model=LLM_PLAN_MODEL,
                temperature=LLM_TEMPERATURE,
                max_completion_tokens=LLM_PLAN_OUTPUT_MAX_TOKENS,
                reasoning_effort=LLM_REASONING_EFFORT.LOW.value,
                api_key=settings.openai_api_key,
            )
        return cls._plan_model

    @classmethod
    def _get_codegen_model(cls) -> ChatOpenAI:
        if cls._codegen_model is None:
            cls._codegen_model = ChatOpenAI(
                model=LLM_CODE_MODEL,
                temperature=LLM_TEMPERATURE,
                max_completion_tokens=LLM_CODEGEN_OUTPUT_MAX_TOKENS,
                reasoning_effort=LLM_REASONING_EFFORT.LOW.value,
                api_key=settings.openai_api_key,
            )
        return cls._codegen_model

    @staticmethod
    def _extract_token_usage(response) -> tuple[int, int, int, int]:
        """Return (input_tokens, output_tokens, total_tokens, reasoning_tokens) from a LangChain response."""
        usage_metadata = getattr(response, "usage_metadata", None) # For raw_response
        if usage_metadata is not None:
            input_tokens = int(usage_metadata.get("input_tokens", 0))
            output_tokens = int(usage_metadata.get("output_tokens", 0))
            total_tokens = int(usage_metadata.get("total_tokens", 0))
            output_details = usage_metadata.get("output_token_details", {})
            reasoning_tokens = int(output_details.get("reasoning", 0))
            return input_tokens, output_tokens, total_tokens, reasoning_tokens

        usage = getattr(response, "usage", None) # For exc.completion
        if usage is not None:
            input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
            output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
            total_tokens = int(getattr(usage, "total_tokens", 0) or 0)
            completion_details = getattr(usage, "completion_tokens_details", None)
            reasoning_tokens = int(getattr(completion_details, "reasoning_tokens", 0) or 0)
            return input_tokens, output_tokens, total_tokens, reasoning_tokens

        raise RuntimeError(
            "Could not extract token usage from LLM response. "
            f"response_type={type(response).__name__}"
        )

    @staticmethod
    def _check_max_tokens(
        call_name: CallType,
        operation: WorkerOperation,
        *,
        input_tokens: int,
        reasoning_tokens: int,
        output_tokens: int,
        total_tokens: int,
        max_tokens: int,
    ) -> None:
        """Warn and raise if output tokens hit the configured max, indicating truncated output."""
        if output_tokens >= max_tokens:
            logger.warning(WorkerLog(
                operation=operation,
                event="LLM call hit max token limit",
                context={
                    "call": call_name.value,
                    "input_tokens": input_tokens,
                    "reasoning_tokens": reasoning_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "max_tokens": max_tokens,
                },
            ))
            raise LLMUsageException(
                f"LLM call '{call_name.value}' hit the max token limit ({max_tokens}). "
                "Output is likely truncated and unusable.",
                total_tokens=total_tokens,
            )

    @staticmethod
    def _extract_text_content(response) -> str:
        """Extract plain text from a response whose content may be a str or a list of typed blocks."""
        content = response.content
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = [
                block["text"]
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            if text_parts:
                return "".join(text_parts)
        raise ValueError(
            f"LLM returned non-text response content. "
            f"type={type(content).__name__!r}, value={content!r}"
        )

    @staticmethod
    def render_plan_prompt(user_request: UserRequest) -> tuple[str, str]:
        """Return (system_prompt, user_query) for the planning LLM call."""
        return PLAN_SYSTEM_PROMPT, str(user_request)

    @staticmethod
    def render_codegen_prompt(plan: VideoPlan) -> tuple[str, str, list[BaseTool]]:
        """Return (system_prompt, user_query) for the codegen LLM call."""
        plan_text = plan.model_dump_json()
        if not any(doc.doc_type == KnowledgeType.SKILL for doc in CORE_DOCUMENTS):
            raise ValueError("Knowledge registry is missing a core skill document.")

        with get_worker_cursor() as cursor:
            candidates = SkillRetrievalService.retrieve(cursor, plan_text)

        candidate_documents = [doc for doc in candidates.all_candidates if doc.document_id in REGISTRY_BY_ID]
        candidate_seeds = {doc.title: REGISTRY_BY_ID[doc.document_id] for doc in candidate_documents}

        core_content = "\n\n".join(read_knowledge_file(doc.path) for doc in CORE_DOCUMENTS)
        candidate_metadata = (
            "\n".join(doc.to_metadata() for doc in candidate_documents)
            if candidate_documents
            else "(No candidate skill documents retrieved.)"
        )
        system_prompt = (
            CODEGEN_SYSTEM_PROMPT
            .replace("{core_content}", core_content)
            .replace("{candidate_metadata}", candidate_metadata)
        )
        return system_prompt, plan_text, [SkillRetrievalService.make_load_skill_document(candidate_seeds)]

    @staticmethod
    def plan_call(system_prompt: str, user_query: str) -> tuple[VideoPlan, int]:
        if IS_E2E_MODE:
            t0 = time.perf_counter()
            duration_ms = int((time.perf_counter() - t0) * 1000)
            logger.info(WorkerLog(
                operation="generate_plan",
                event="LLM call finished [E2E MODE]",
                context={
                    "call": CallType.PLAN.value, "model": LLM_PLAN_MODEL,
                    "input_tokens": 0, "reasoning_tokens": 0,
                    "output_tokens": 0, "total_tokens": 0, "duration_ms": duration_ms,
                },
            ))
            return STUB_PLAN, 0

        model = LLMService._get_plan_model()
        structured_model = model.with_structured_output(VideoPlan, include_raw=True)
        t0 = time.perf_counter()
        try:
            result = structured_model.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query),
            ])
        except LengthFinishReasonError as exc:
            duration_ms = int((time.perf_counter() - t0) * 1000)
            input_tok, output_tok, total_tok, reasoning_tok = LLMService._extract_token_usage(exc.completion)
            logger.warning(WorkerLog(
                operation="generate_plan",
                event="LLM call failed: length finish reason",
                context={
                    "call": CallType.PLAN.value, "model": LLM_PLAN_MODEL,
                    "input_tokens": input_tok, "reasoning_tokens": reasoning_tok,
                    "output_tokens": output_tok, "total_tokens": total_tok,
                    "duration_ms": duration_ms, "reason": "length_finish_reason",
                },
            ))
            raise LLMUsageException(
                f"LLM call '{CallType.PLAN.value}' exhausted its output token budget "
                f"({LLM_PLAN_OUTPUT_MAX_TOKENS}) before producing a usable plan.",
                total_tokens=total_tok,
            ) from exc
        except Exception as exc:
            duration_ms = int((time.perf_counter() - t0) * 1000)
            logger.warning(WorkerLog(
                operation="generate_plan",
                event="LLM call failed",
                context={
                    "call": CallType.PLAN.value, "model": LLM_PLAN_MODEL,
                    "duration_ms": duration_ms, "reason": type(exc).__name__,
                },
            ))
            raise RuntimeError(
                f"LLM call '{CallType.PLAN.value}' failed before producing a usable plan: {type(exc).__name__}",
            ) from exc
        duration_ms = int((time.perf_counter() - t0) * 1000)
        raw_response = result.get("raw") if isinstance(result, dict) else None
        input_tok, output_tok, total_tok, reasoning_tok = LLMService._extract_token_usage(raw_response)
        LLMService._check_max_tokens(
            CallType.PLAN,
            "generate_plan",
            input_tokens=input_tok,
            reasoning_tokens=reasoning_tok,
            output_tokens=output_tok,
            total_tokens=total_tok,
            max_tokens=LLM_PLAN_OUTPUT_MAX_TOKENS,
        )
        logger.info(WorkerLog(
            operation="generate_plan",
            event="LLM call finished",
            context={
                "call": CallType.PLAN.value, "model": LLM_PLAN_MODEL,
                "input_tokens": input_tok, "reasoning_tokens": reasoning_tok,
                "output_tokens": output_tok, "total_tokens": total_tok,
                "duration_ms": duration_ms,
            },
        ))
        if not isinstance(result, dict):
            logger.warning(WorkerLog(
                operation="generate_plan",
                event="LLM output validation failed: unexpected response shape",
                context={"response_type": type(result).__name__},
            ))
            raise LLMUsageException(
                f"LLM output validation failed: structured response has an unexpected shape (response_type={type(result).__name__}, expected dict).",
                total_tokens=total_tok,
            )

        plan = result.get("parsed")
        if isinstance(plan, VideoPlan):
            for scene in plan.scenes:
                if scene.scene_number == -1:
                    logger.warning(WorkerLog(
                        operation="generate_plan",
                        event="LLM output validation failed: non-math topic detected",
                        context={"learning_objective": scene.learning_objective},
                    ))
                    raise LLMUsageException(
                        f"LLM output validation failed: non-math topic detected ({scene.learning_objective})",
                        total_tokens=total_tok,
                    )
            return plan, total_tok

        logger.warning(WorkerLog(
            operation="generate_plan",
            event="LLM output validation failed: response is not a valid instance",
            context={"parsed_type": type(plan).__name__},
        ))
        raise LLMUsageException(
            f"LLM output validation failed: response is not a valid instance (parsed_type={type(plan).__name__}, expected VideoPlan).",
            total_tokens=total_tok,
        )

    @staticmethod
    def codegen_call(system_prompt: str, user_query: str, tools: list[BaseTool] | None = None) -> tuple[str, int]:
        if IS_E2E_MODE:
            t0 = time.perf_counter()
            duration_ms = int((time.perf_counter() - t0) * 1000)
            logger.info(WorkerLog(
                operation="generate_code",
                event="LLM call finished [E2E MODE]",
                context={
                    "call": CallType.CODEGEN.value, "model": LLM_CODE_MODEL,
                    "input_tokens": 0, "reasoning_tokens": 0,
                    "output_tokens": 0, "total_tokens": 0, "duration_ms": duration_ms,
                },
            ))
            return STUB_BROKEN_CODE, 0

        if not tools:
            raise ValueError("codegen_call requires tools for non-E2E code generation.")

        t0 = time.perf_counter()
        model_with_tools = LLMService._get_codegen_model().bind_tools(tools)
        tools_by_name: dict[str, BaseTool] = {t.name: t for t in tools}
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_query)]
        input_tokens = 0
        output_tokens = 0
        reasoning_tokens = 0
        total_tokens = 0
        tool_usage = CodegenToolUsage()
        for tool in tools:
            if tool.metadata and "available_optional_titles" in tool.metadata:
                tool_usage.available_optional_titles = tool.metadata["available_optional_titles"]
                break

        for _ in range(MAX_TOOL_CALL_ITERATIONS):
            try:
                response: AIMessage = model_with_tools.invoke(messages)
            except LengthFinishReasonError as exc:
                duration_ms = int((time.perf_counter() - t0) * 1000)
                input_tok, output_tok, total_tok, reasoning_tok = LLMService._extract_token_usage(exc.completion)
                logger.warning(WorkerLog(
                    operation="generate_code",
                    event="LLM call failed: length finish reason",
                    context={
                        "call": CallType.CODEGEN.value, "model": LLM_CODE_MODEL,
                        "input_tokens": input_tok, "reasoning_tokens": reasoning_tok,
                        "output_tokens": output_tok, "total_tokens": total_tok,
                        "duration_ms": duration_ms, "reason": "length_finish",
                    },
                ))
                raise LLMUsageException(
                    f"LLM call '{CallType.CODEGEN.value}' hit the token limit ({LLM_CODEGEN_OUTPUT_MAX_TOKENS}) before finishing output.",
                    total_tokens=total_tokens + total_tok,
                ) from exc
            except Exception as exc:
                duration_ms = int((time.perf_counter() - t0) * 1000)
                logger.warning(WorkerLog(
                    operation="generate_code",
                    event="LLM call failed",
                    context={
                        "call": CallType.CODEGEN.value, "model": LLM_CODE_MODEL,
                        "duration_ms": duration_ms, "reason": type(exc).__name__,
                    },
                ))
                raise RuntimeError(
                    f"LLM call '{CallType.CODEGEN.value}' failed before producing code: {type(exc).__name__}",
                ) from exc

            input_tok, output_tok, iter_total, reasoning_tok = LLMService._extract_token_usage(response)
            input_tokens += input_tok
            output_tokens += output_tok
            reasoning_tokens += reasoning_tok
            total_tokens += iter_total
            tool_usage.model_iterations += 1
            tool_calls = response.tool_calls
            if not tool_calls:
                duration_ms = int((time.perf_counter() - t0) * 1000)
                LLMService._check_max_tokens(
                    CallType.CODEGEN,
                    "generate_code",
                    input_tokens=input_tok,
                    reasoning_tokens=reasoning_tok,
                    output_tokens=output_tok,
                    total_tokens=total_tokens,
                    max_tokens=LLM_CODEGEN_OUTPUT_MAX_TOKENS,
                )
                logger.info(WorkerLog(
                    operation="generate_code",
                    event="LLM call finished",
                    context={
                        "call": CallType.CODEGEN.value, "model": LLM_CODE_MODEL,
                        "input_tokens": input_tokens, "reasoning_tokens": reasoning_tokens,
                        "output_tokens": output_tokens, "total_tokens": total_tokens,
                        "duration_ms": duration_ms,
                        "tool_usage": tool_usage.model_dump(),
                    },
                ))
                try:
                    return LLMService._extract_text_content(response), total_tokens
                except Exception as exc:
                    raise LLMUsageException(
                        "LLM output validation failed: codegen response did not contain plain text content.",
                        total_tokens=total_tokens,
                    ) from exc

            messages.append(response)
            tool_usage.tool_call_iterations += 1
            for tool_call in tool_calls:
                tool_args = tool_call.get("args", {})
                title = str(tool_args.get("title", "")) if isinstance(tool_args, dict) else ""
                tool_usage.total_requested_tool_calls += 1
                tool_usage.requested_titles.append(title)
                try:
                    tool_name = tool_call["name"]
                    result = tools_by_name[tool_name].invoke(tool_args)
                    if isinstance(result, str) and result.startswith("Error:"):
                        if SkillRetrievalService.UNKNOWN_OR_NON_CANDIDATE_ERROR in result:
                            tool_usage.unknown_or_non_candidate_count += 1
                        elif SkillRetrievalService.DUPLICATE_LOAD_ERROR in result:
                            tool_usage.duplicate_count += 1
                        elif SkillRetrievalService.LOAD_LIMIT_ERROR in result:
                            tool_usage.load_limit_count += 1
                        else:
                            tool_usage.tool_execution_error_count += 1
                    else:
                        tool_usage.successful_optional_load_count += 1
                        tool_usage.loaded_titles.append(title)
                    messages.append(ToolMessage(content=result, tool_call_id=tool_call["id"]))
                except Exception as exc:
                    tool_usage.tool_execution_error_count += 1
                    raise LLMUsageException(
                        f"LLM call '{CallType.CODEGEN.value}' failed while executing a requested tool: {type(exc).__name__}",
                        total_tokens=total_tokens,
                    ) from exc

        logger.warning(WorkerLog(
            operation="generate_code",
            event="LLM call exceeded tool-call iteration limit",
            context={
                "call": CallType.CODEGEN.value,
                "model": LLM_CODE_MODEL,
                "total_tokens": total_tokens,
                "max_tool_call_iterations": MAX_TOOL_CALL_ITERATIONS,
                "tool_usage": tool_usage.model_dump(),
            },
        ))
        raise LLMUsageException(
            f"LLM call '{CallType.CODEGEN.value}' exceeded tool-call iteration limit ({MAX_TOOL_CALL_ITERATIONS}).",
            total_tokens=total_tokens,
        )

    @staticmethod
    def render_fix_prompt(code: str, error_context: str) -> tuple[str, str]:
        user_query = (
            f"Fix this Manim code:\n\n"
            f"<code>\n{code}\n</code>\n\n"
            f"It failed with this error:\n"
            f"<error>\n{error_context}\n</error>\n\n"
        )
        return CODEGEN_FIX_SYSTEM_PROMPT, user_query

    @staticmethod
    def fix_call(system_prompt: str, user_query: str) -> tuple[str, int]:
        if IS_E2E_MODE:
            t0 = time.perf_counter()
            duration_ms = int((time.perf_counter() - t0) * 1000)
            logger.info(WorkerLog(
                operation="fix_code",
                event="LLM call finished [E2E MODE]",
                context={
                    "call": CallType.FIX.value, "model": LLM_CODE_MODEL,
                    "input_tokens": 0, "reasoning_tokens": 0,
                    "output_tokens": 0, "total_tokens": 0, "duration_ms": duration_ms,
                },
            ))
            return STUB_FIXED_CODE, 0

        model = LLMService._get_codegen_model()
        t0 = time.perf_counter()
        try:
            response: AIMessage = model.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query),
            ])
        except LengthFinishReasonError as exc:
            duration_ms = int((time.perf_counter() - t0) * 1000)
            input_tok, output_tok, total_tok, reasoning_tok = LLMService._extract_token_usage(exc.completion)
            logger.warning(WorkerLog(
                operation="fix_code",
                event="LLM call failed: length finish reason",
                context={
                    "call": CallType.FIX.value, "model": LLM_CODE_MODEL,
                    "input_tokens": input_tok, "reasoning_tokens": reasoning_tok,
                    "output_tokens": output_tok, "total_tokens": total_tok,
                    "duration_ms": duration_ms, "reason": "length_finish",
                },
            ))
            raise LLMUsageException(
                f"LLM call '{CallType.FIX.value}' hit the token limit ({LLM_CODEGEN_OUTPUT_MAX_TOKENS}) before finishing output.",
                total_tokens=total_tok,
            ) from exc
        except Exception as exc:
            duration_ms = int((time.perf_counter() - t0) * 1000)
            logger.warning(WorkerLog(
                operation="fix_code",
                event="LLM call failed",
                context={
                    "call": CallType.FIX.value, "model": LLM_CODE_MODEL,
                    "duration_ms": duration_ms, "reason": type(exc).__name__,
                },
            ))
            raise RuntimeError(
                f"LLM call '{CallType.FIX.value}' failed before producing fixed code: {type(exc).__name__}",
            ) from exc
        duration_ms = int((time.perf_counter() - t0) * 1000)
        input_tok, output_tok, total_tok, reasoning_tok = LLMService._extract_token_usage(response)
        LLMService._check_max_tokens(
            CallType.FIX,
            "fix_code",
            input_tokens=input_tok,
            reasoning_tokens=reasoning_tok,
            output_tokens=output_tok,
            total_tokens=total_tok,
            max_tokens=LLM_CODEGEN_OUTPUT_MAX_TOKENS,
        )
        logger.info(WorkerLog(
            operation="fix_code",
            event="LLM call finished",
            context={
                "call": CallType.FIX.value, "model": LLM_CODE_MODEL,
                "input_tokens": input_tok, "reasoning_tokens": reasoning_tok,
                "output_tokens": output_tok, "total_tokens": total_tok,
                "duration_ms": duration_ms,
            },
        ))
        try:
            return LLMService._extract_text_content(response), total_tok
        except ValueError as exc:
            logger.warning(WorkerLog(
                operation="fix_code",
                event="LLM output validation failed: no plain text content",
            ))
            raise LLMUsageException(
                "LLM output validation failed: fix response did not contain plain text content.",
                total_tokens=total_tok,
            ) from exc
