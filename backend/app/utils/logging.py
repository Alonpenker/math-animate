import sys
from typing import Any, Literal
import structlog
from pydantic import BaseModel

from app.utils.seq_processor import SeqProcessor


class BaseLog(BaseModel):
    event: str
    job_id: str | None = None
    call_id: str | None = None
    error: dict[str, str] | None = None
    context: dict | None = None


WorkerOperation = Literal[
    "generate_plan", "generate_code", "generate_render", "seed_knowledge",
    "e2e_mode"
]

APIOperation = Literal[
    "health_check", "create_job", "get_job_status", "get_job_plan",
    "approve_job", "cancel_job", "list_artifacts", "get_artifact",
    "download_artifact", "list_knowledge", "get_knowledge_document",
    "get_usage_summary", "delete_artifact", "seed_knowledge", "migrate_schema",
]

class WorkerLog(BaseLog):
    operation: WorkerOperation

class APILog(BaseLog):
    operation: APIOperation


class ConsoleRenderer:
    def __call__(self, _logger: Any, _method: str, event_dict: structlog.types.EventDict) -> str:
        skip = {"event", "service", "operation", "level", "timestamp"}
        timestamp = event_dict.get("timestamp", "")
        level = event_dict.get("level", "").upper()
        service = event_dict.get("service", "?")
        operation = event_dict.get("operation", "?")
        event = event_dict.get("event", "")
        extras = {k: v for k, v in event_dict.items() if k not in skip and v is not None}
        kv = " ".join(f"{k}={v}" for k, v in extras.items())
        prefix = f"[{service}][{operation}]"
        body = f"{prefix} {event} | {kv}" if kv else f"{prefix} {event}"
        return f"{timestamp} | {level:<7} | {body}"


class Logger:
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
            SeqProcessor(),
            ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(10),  # DEBUG level
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    def __init__(self, _logger: Any) -> None:
        self._logger = _logger

    @classmethod
    def get_logger(cls, service: Literal["api", "worker"]) -> "Logger":
        return cls(structlog.get_logger().bind(service=service))

    @staticmethod
    def serialize_error(exc: BaseException) -> dict[str, str]:
        return {"type": type(exc).__name__, "message": str(exc)}

    def _log(self, method: str, log: BaseLog, exc_info: BaseException | bool = False) -> None:
        fields = log.model_dump(exclude_none=True)
        event_msg = fields.pop("event")
        if exc_info and "error" not in fields:
            if isinstance(exc_info, BaseException):
                fields["error"] = Logger.serialize_error(exc_info)
            elif exc_info is True:
                exc = sys.exc_info()[1]
                if exc is not None:
                    fields["error"] = Logger.serialize_error(exc)
        getattr(self._logger, method)(event_msg, **fields)

    def debug(self, log: BaseLog) -> None:
        self._log("debug", log)

    def info(self, log: BaseLog) -> None:
        self._log("info", log)

    def warning(self, log: BaseLog, exc_info: BaseException | bool = False) -> None:
        self._log("warning", log, exc_info=exc_info)

    def error(self, log: BaseLog, exc_info: BaseException | bool = False) -> None:
        self._log("error", log, exc_info=exc_info)
