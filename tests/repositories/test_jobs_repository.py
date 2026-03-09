"""
JobsRepository tests.

JobsRepository is Redis-backed (not SQL).  Tests use FakeRedis so no real
Redis connection is required.
"""
from uuid import uuid4

from app.dependencies.redis_client import TERMINAL_JOB_TTL_SECONDS
from app.domain.job_state import JobStatus
from app.repositories.jobs_repository import JobsRepository, TERMINAL_STATUSES
from app.schemas.jobs import Job

from tests.repositories.conftest import FakeRedis


# ─────────────────────────────────────────────────────────────────────────────
# JobsRepository.create_job
# ─────────────────────────────────────────────────────────────────────────────

def test_create_job_stores_status_string_in_redis():
    # Given
    r = FakeRedis()
    job_id = uuid4()
    job = Job(job_id=job_id, status=JobStatus.CREATED)

    # When
    JobsRepository.create_job(r, job)

    # Then
    assert r.get(f"job:{job_id}") == b"CREATED"


# ─────────────────────────────────────────────────────────────────────────────
# JobsRepository.get_job
# ─────────────────────────────────────────────────────────────────────────────

def test_get_job_returns_job_with_correct_id_and_status():
    # Given
    r = FakeRedis()
    job_id = uuid4()
    r.set(f"job:{job_id}", "PLANNING")

    # When
    result = JobsRepository.get_job(r, job_id)

    # Then
    assert result is not None
    assert result.job_id == job_id
    assert result.status == JobStatus.PLANNING


def test_get_job_returns_none_when_key_absent_from_redis():
    # Given
    r = FakeRedis()
    job_id = uuid4()

    # When
    result = JobsRepository.get_job(r, job_id)

    # Then
    assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# JobsRepository.update_job_status
# ─────────────────────────────────────────────────────────────────────────────

def test_update_job_status_sets_new_status_without_ttl_for_non_terminal_status():
    # Given
    r = FakeRedis()
    job_id = uuid4()

    # When
    JobsRepository.update_job_status(r, job_id, JobStatus.PLANNING)

    # Then
    assert r.get(f"job:{job_id}") == b"PLANNING"
    assert r.get_ttl(f"job:{job_id}") is None


def test_update_job_status_sets_ttl_when_status_is_terminal():
    # Given
    r = FakeRedis()
    job_id = uuid4()

    # When
    JobsRepository.update_job_status(r, job_id, JobStatus.RENDERED)

    # Then
    assert r.get_ttl(f"job:{job_id}") == TERMINAL_JOB_TTL_SECONDS


def test_update_job_status_applies_ttl_for_every_terminal_status():
    # Given
    r = FakeRedis()

    # When / Then
    for status in TERMINAL_STATUSES:
        job_id = uuid4()
        JobsRepository.update_job_status(r, job_id, status)
        assert r.get_ttl(f"job:{job_id}") == TERMINAL_JOB_TTL_SECONDS, (
            f"Expected TTL for terminal status {status}"
        )


def test_terminal_statuses_include_failed_quota_exceeded():
    assert JobStatus.FAILED_QUOTA_EXCEEDED in TERMINAL_STATUSES
