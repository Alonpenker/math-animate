import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from settings import LogFileNames, RunFolderNames


LogLevel = Literal["debug", "info", "warning", "error"]


@dataclass
class LabLog:
    operation: str
    event: str
    context: dict | None = None
    error: dict[str, str] | None = None


class LabLogger:
    def __init__(self, *, service: str = "ai_workflow_lab", run_dir: Path | None = None) -> None:
        self.service = service
        self.run_dir = run_dir

    def bind(self, *, run_dir: Path | None = None) -> "LabLogger":
        return LabLogger(service=self.service, run_dir=run_dir or self.run_dir)

    @staticmethod
    def serialize_error(exc: BaseException) -> dict[str, str]:
        return {"type": type(exc).__name__, "message": str(exc)}

    def debug(self, log: LabLog) -> None:
        self._log("debug", log)

    def info(self, log: LabLog) -> None:
        self._log("info", log)

    def warning(self, log: LabLog, exc_info: BaseException | bool = False) -> None:
        self._log("warning", log, exc_info=exc_info)

    def error(self, log: LabLog, exc_info: BaseException | bool = False) -> None:
        self._log("error", log, exc_info=exc_info)

    def _log(
        self,
        level: LogLevel,
        log: LabLog,
        exc_info: BaseException | bool = False,
    ) -> None:
        error = log.error
        if error is None and isinstance(exc_info, BaseException):
            error = self.serialize_error(exc_info)

        rendered = self._render(level, log, error)
        print(rendered, flush=True)

        if self.run_dir is not None:
            logs_dir = self.run_dir / RunFolderNames.LOGS
            logs_dir.mkdir(parents=True, exist_ok=True)
            with (logs_dir / LogFileNames.WORKFLOW).open("a", encoding="utf-8") as handle:
                handle.write(rendered + "\n")

    def _render(
        self,
        level: LogLevel,
        log: LabLog,
        error: dict[str, str] | None,
    ) -> str:
        timestamp = datetime.now().isoformat(timespec="seconds")
        prefix = f"[{self.service}][{log.operation}]"
        extras = []
        if log.context:
            extras.extend(f"{key}={self._format_value(value)}" for key, value in log.context.items())
        if error:
            extras.append(f"error={self._format_value(error)}")
        suffix = f" | {' '.join(extras)}" if extras else ""
        return f"{timestamp} | {level.upper():<7} | {prefix} {log.event}{suffix}"

    @staticmethod
    def _format_value(value: object) -> str:
        if isinstance(value, (str, int, float, bool)) or value is None:
            text = str(value)
        else:
            text = json.dumps(value, ensure_ascii=True, separators=(",", ":"))
        if len(text) > 700:
            return text[:697] + "..."
        return text


logger = LabLogger()
