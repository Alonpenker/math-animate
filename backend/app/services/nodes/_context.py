import time
from dataclasses import dataclass, field
from uuid import UUID

from app.configs.llm_settings import LLM_PROVIDER, LLM_REASONING_EFFORT, OPENROUTER_MODELS
from app.domain.job_state import JobStatus
from app.services.openrouter_service import CallType, OpenRouterTokenUsage
from app.utils.logging import Logger, WorkerLog
from app.workers.worker_helpers import transition_job

logger = Logger.get_logger("worker")


@dataclass
class CodegenContext:
    job_id: UUID
    current_status: JobStatus
    _call_number: int = field(default=0, init=False)
    candidates_by_title: dict = field(default_factory=dict, init=False)
    selected_titles: list = field(default_factory=list, init=False)

    def set_status(self, from_status: JobStatus, to_status: JobStatus) -> None:
        transition_job(self.job_id, from_status, to_status)
        self.current_status = to_status

    def log_node_started(self, name: str) -> None:
        logger.info(WorkerLog(
            operation="generate_code",
            event=f"Node: {name} started",
            job_id=str(self.job_id),
        ))

    def log_openrouter_call(
        self,
        call_type: CallType,
        started_at: float,
        usage: OpenRouterTokenUsage,
        extra_context: dict | None = None,
        model: OPENROUTER_MODELS = OPENROUTER_MODELS.CODING_MODEL,
        reasoning_effort: LLM_REASONING_EFFORT | None = None,
    ) -> None:
        self._call_number += 1
        context = {
            "provider": LLM_PROVIDER.OPENROUTER.value,
            "model": model.value,
            "call_type": call_type.value,
            "call_number": self._call_number,
            "duration_ms": int((time.perf_counter() - started_at) * 1000),
            "input_tokens": usage.input_tokens,
            "reasoning_tokens": usage.reasoning_tokens,
            "output_tokens": usage.output_tokens,
            "total_tokens": usage.total_tokens,
        }
        if reasoning_effort is not None:
            context["requested_reasoning_effort"] = reasoning_effort.value
        if extra_context:
            context.update(extra_context)
        logger.info(WorkerLog(
            operation="generate_code",
            event="OpenRouter call completed",
            job_id=str(self.job_id),
            context=context,
        ))
