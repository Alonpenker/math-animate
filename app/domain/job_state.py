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
    RENDER_QUEUED = "RENDER_QUEUED"
    RENDERING = "RENDERING"
    RENDERED = "RENDERED"
    FAILED_PLANNING = "FAILED_PLANNING"
    FAILED_CODEGEN = "FAILED_CODEGEN"
    FAILED_RENDER = "FAILED_RENDER"
    CANCELLED = "CANCELLED"

ALLOWED_TRANSITIONS: Dict[JobStatus, FrozenSet[JobStatus]] = {
    JobStatus.CREATED: frozenset({JobStatus.PLANNING, JobStatus.CANCELLED}),
    JobStatus.PLANNING: frozenset({JobStatus.PLANNED, JobStatus.FAILED_PLANNING}),
    JobStatus.PLANNED: frozenset({JobStatus.APPROVED, JobStatus.CANCELLED}),
    JobStatus.APPROVED: frozenset({JobStatus.CODEGEN, JobStatus.CANCELLED}),
    JobStatus.CODEGEN: frozenset({JobStatus.CODED, JobStatus.FAILED_CODEGEN}),
    JobStatus.CODED: frozenset({JobStatus.RENDERING, JobStatus.CANCELLED}),
    JobStatus.RENDERING: frozenset({JobStatus.RENDERED, JobStatus.FAILED_RENDER}),
    JobStatus.RENDERED: frozenset({JobStatus.CANCELLED}),
    JobStatus.FAILED_PLANNING: frozenset({JobStatus.CANCELLED}),
    JobStatus.FAILED_CODEGEN: frozenset({JobStatus.CANCELLED}),
    JobStatus.FAILED_RENDER: frozenset({JobStatus.CANCELLED}),
    JobStatus.CANCELLED: frozenset()
}


def can_transition(current: JobStatus, target: JobStatus) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, frozenset())

def require_transition(current: JobStatus, target: JobStatus) -> None:
    if not can_transition(current, target):
        raise InvalidTransitionError(
            f"Invalid transition from {current.value} to {target.value}"
        )
