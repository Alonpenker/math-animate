from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lab_logging import LabLog, logger
from runtime.files import RunFiles
from runtime.usage import UsageTracker
from services.llm import LlmGateway, create_llm_gateway
from settings import E2E_RUN_NAME


@dataclass(frozen=True)
class ExperimentContext:
    request_path: Path
    request_text: str
    provided_plan_path: Path | None
    e2e: bool
    llm: LlmGateway
    files: RunFiles
    usage: UsageTracker
    run_logger: Any

    @classmethod
    def create(
        cls,
        *,
        request_path: Path,
        name: str | None,
        provided_plan_path: Path | None,
        e2e: bool = False,
    ) -> "ExperimentContext":
        request_text = request_path.read_text(encoding="utf-8").strip()
        run_name = E2E_RUN_NAME if e2e else name
        files = RunFiles.create(run_name, overwrite=e2e)
        files.write_request(request_text)
        ctx = cls(
            request_path=request_path,
            request_text=request_text,
            provided_plan_path=provided_plan_path,
            e2e=e2e,
            llm=create_llm_gateway(e2e=e2e),
            files=files,
            usage=UsageTracker(files),
            run_logger=logger.bind(run_dir=files.run_dir),
        )
        ctx.run_logger.info(LabLog(
            operation="experiment",
            event="Experiment started",
            context={
                "run_dir": str(files.run_dir),
                "request_path": str(request_path),
                "provided_plan_path": str(provided_plan_path) if provided_plan_path else "",
                "e2e": e2e,
            },
        ))
        return ctx

    def write_summary(self, data: dict) -> None:
        self.files.write_summary(data, self.usage.summary())
