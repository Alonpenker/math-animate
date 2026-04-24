from enum import Enum
from typing import Dict, FrozenSet

from app.exceptions.invalid_transition_error import InvalidTransitionError


class JobStatus(str, Enum):
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    PLANNED = "PLANNED"
    APPROVED = "APPROVED"
    CODEGEN = "CODEGEN"
    CODED = "CODED"
    RENDERING = "RENDERING"
    RENDERED = "RENDERED"
    FAILED_PLANNING = "FAILED_PLANNING"
    FAILED_CODEGEN = "FAILED_CODEGEN"
    FAILED_RENDER = "FAILED_RENDER"
    FAILED_QUOTA_EXCEEDED = "FAILED_QUOTA_EXCEEDED"
    FAILED_LLM_USAGE = "FAILED_LLM_USAGE"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    FIXING = "FIXING"
    FAILED_VERIFICATION = "FAILED_VERIFICATION"
    CANCELLED = "CANCELLED"

ALLOWED_TRANSITIONS: Dict[JobStatus, FrozenSet[JobStatus]] = {
    JobStatus.CREATED: frozenset({JobStatus.PLANNING}),
    JobStatus.PLANNING: frozenset({
        JobStatus.PLANNED,
        JobStatus.FAILED_PLANNING,
        JobStatus.FAILED_QUOTA_EXCEEDED,
        JobStatus.FAILED_LLM_USAGE,
    }),
    JobStatus.PLANNED: frozenset({JobStatus.APPROVED, JobStatus.CANCELLED}),
    JobStatus.APPROVED: frozenset({JobStatus.CODEGEN}),
    JobStatus.CODEGEN: frozenset({
        JobStatus.CODED,
        JobStatus.FAILED_CODEGEN,
        JobStatus.FAILED_QUOTA_EXCEEDED,
        JobStatus.FAILED_LLM_USAGE,
    }),
    JobStatus.CODED: frozenset({JobStatus.VERIFYING}),
    JobStatus.VERIFYING: frozenset({JobStatus.VERIFIED, JobStatus.FIXING, JobStatus.FAILED_VERIFICATION}),
    JobStatus.VERIFIED: frozenset({JobStatus.RENDERING}),
    JobStatus.FIXING: frozenset({
        JobStatus.VERIFYING,
        JobStatus.FAILED_VERIFICATION,
        JobStatus.FAILED_QUOTA_EXCEEDED,
        JobStatus.FAILED_LLM_USAGE,
    }),
    JobStatus.RENDERING: frozenset({JobStatus.RENDERED, JobStatus.FAILED_RENDER}),
    JobStatus.RENDERED: frozenset(),
    JobStatus.FAILED_PLANNING: frozenset(),
    JobStatus.FAILED_CODEGEN: frozenset(),
    JobStatus.FAILED_RENDER: frozenset(),
    JobStatus.FAILED_QUOTA_EXCEEDED: frozenset(),
    JobStatus.FAILED_LLM_USAGE: frozenset(),
    JobStatus.FAILED_VERIFICATION: frozenset(),
    JobStatus.CANCELLED: frozenset()
}


def can_transition(current: JobStatus, target: JobStatus) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, frozenset())

def require_transition(current: JobStatus, target: JobStatus) -> None:
    if not can_transition(current, target):
        raise InvalidTransitionError(
            f"Invalid transition from {current.value} to {target.value}"
        )
