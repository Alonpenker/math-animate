import pytest

from domain.job_state import JobStatus, InvalidTransitionError, require_transition


def test_valid_transitions():
    require_transition(JobStatus.CREATED, JobStatus.PLANNING)
    require_transition(JobStatus.PLANNING, JobStatus.PLANNED)
    require_transition(JobStatus.PLANNED, JobStatus.APPROVED)
    require_transition(JobStatus.APPROVED, JobStatus.CODEGEN)
    require_transition(JobStatus.CODEGEN, JobStatus.CODED)
    require_transition(JobStatus.CODED, JobStatus.RENDER_QUEUED)
    require_transition(JobStatus.RENDER_QUEUED, JobStatus.RENDERING)
    require_transition(JobStatus.RENDERING, JobStatus.RENDERED)


def test_invalid_transition_raises():
    with pytest.raises(InvalidTransitionError):
        require_transition(JobStatus.CREATED, JobStatus.RENDERING)
