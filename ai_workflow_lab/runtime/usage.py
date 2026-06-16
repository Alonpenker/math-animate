import json

from lab_logging import LabLog
from runtime.files import RunFiles
from services.llm import TokenUsage
from settings import UsageFileNames


class UsageTracker:
    def __init__(self, files: RunFiles) -> None:
        self.files = files

    def record(self, filename: str, usage: TokenUsage, duration_ms: int) -> dict:
        call_usage = {
            "filename": filename,
            "duration_ms": duration_ms,
            "input_tokens": usage.input_tokens,
            "reasoning_tokens": usage.reasoning_tokens,
            "output_tokens": usage.output_tokens,
            "total_tokens": usage.total_tokens,
        }
        self.files.write_log_json(filename, call_usage)
        self.files.append_log_line(
            UsageFileNames.TOKEN_USAGE_JSONL,
            json.dumps(call_usage),
        )

        summary = self.summary() or {
            "call_count": 0,
            "duration_ms": 0,
            "input_tokens": 0,
            "reasoning_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }
        summary["call_count"] += 1
        summary["duration_ms"] += int(call_usage["duration_ms"])
        summary["input_tokens"] += usage.input_tokens
        summary["reasoning_tokens"] += usage.reasoning_tokens
        summary["output_tokens"] += usage.output_tokens
        summary["total_tokens"] += usage.total_tokens
        self.files.write_log_json(UsageFileNames.TOKEN_USAGE_SUMMARY, summary)
        return summary

    def summary(self) -> dict | None:
        return self.files.read_log_json(UsageFileNames.TOKEN_USAGE_SUMMARY)

    @staticmethod
    def log_llm_completed(
        run_logger,
        *,
        operation: str,
        model: str,
        duration_ms: int,
        usage: TokenUsage,
        cumulative_usage: dict,
        extra_context: dict | None = None,
    ) -> None:
        context = {
            "model": model,
            "duration_ms": duration_ms,
            "input_tokens": usage.input_tokens,
            "reasoning_tokens": usage.reasoning_tokens,
            "output_tokens": usage.output_tokens,
            "total_tokens": usage.total_tokens,
            "cumulative_total_tokens": cumulative_usage["total_tokens"],
        }
        if extra_context:
            context.update(extra_context)
        run_logger.info(LabLog(
            operation=operation,
            event="OpenRouter call completed",
            context=context,
        ))
