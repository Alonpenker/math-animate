from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.domain.job_state import JobStatus
from app.schemas.jobs import Job
from app.schemas.plan import Plan


# ─────────────────────────────────────────────────────────────────────────────
# create_job
# ─────────────────────────────────────────────────────────────────────────────

def test_create_job_persists_created_status_and_enqueues_worker(
    jobs_routes_with_runner_mock,
    sample_user_request,
    fake_cursor,
    test_store,
):
    # Given
    fake_redis = object()

    # When
    response = jobs_routes_with_runner_mock.create_job(
        request=object(), user_request=sample_user_request, redis_client=fake_redis, cursor=fake_cursor
    )

    # Then
    assert response.job.status == JobStatus.CREATED
    assert response.job.job_id in test_store["jobs"]
    assert test_store["jobs"][response.job.job_id].status == JobStatus.CREATED
    assert len(test_store["worker_runner_calls"]) == 1
    runner_call = test_store["worker_runner_calls"][0]
    assert runner_call.job.job_id == response.job.job_id
    assert runner_call.user_request.topic == sample_user_request.topic


# ─────────────────────────────────────────────────────────────────────────────
# get_job_status
# ─────────────────────────────────────────────────────────────────────────────

def test_get_job_status_returns_current_status(
    jobs_routes_with_runner_mock,
    fake_cursor,
    test_store,
):
    # Given
    job = Job(status=JobStatus.PLANNED)
    test_store["jobs"][job.job_id] = job
    fake_redis = object()

    # When
    response = jobs_routes_with_runner_mock.get_job_status(
        request=object(), job_id=job.job_id, redis_client=fake_redis
    )

    # Then
    assert response.job.job_id == job.job_id
    assert response.job.status == JobStatus.PLANNED


def test_get_job_status_raises_404_when_job_does_not_exist(
    jobs_routes_with_runner_mock,
    fake_cursor,
):
    # Given
    missing_id = uuid4()
    fake_redis = object()

    # When / Then
    with pytest.raises(HTTPException) as exc_info:
        jobs_routes_with_runner_mock.get_job_status(request=object(), job_id=missing_id, redis_client=fake_redis)

    assert exc_info.value.status_code == 404
    assert "Job not found" in exc_info.value.detail


# ─────────────────────────────────────────────────────────────────────────────
# get_plan
# ─────────────────────────────────────────────────────────────────────────────

def test_get_plan_returns_job_and_plan_data(
    jobs_routes_with_runner_mock,
    fake_cursor,
    sample_video_plan,
    test_store,
):
    # Given
    job = Job(status=JobStatus.PLANNED)
    test_store["jobs"][job.job_id] = job
    test_store["plans"][job.job_id] = Plan(
        job_id=job.job_id, plan=sample_video_plan, approved=False
    )

    # When
    response = jobs_routes_with_runner_mock.get_plan(
        request=object(), job_id=job.job_id, redis_client=object(), cursor=fake_cursor
    )

    # Then
    assert response.job.job_id == job.job_id
    assert response.job.status == JobStatus.PLANNED
    assert response.data.job_id == job.job_id


def test_get_plan_raises_404_when_plan_not_yet_created(
    jobs_routes_with_runner_mock,
    fake_cursor,
    test_store,
):
    # Given
    job = Job(status=JobStatus.PLANNED)
    test_store["jobs"][job.job_id] = job
    # No plan in test_store

    # When / Then
    with pytest.raises(HTTPException) as exc_info:
        jobs_routes_with_runner_mock.get_plan(
            request=object(), job_id=job.job_id, redis_client=object(), cursor=fake_cursor
        )

    assert exc_info.value.status_code == 404
    assert "Plan not found" in exc_info.value.detail


# ─────────────────────────────────────────────────────────────────────────────
# approve_plan
# ─────────────────────────────────────────────────────────────────────────────

def test_approve_plan_with_true_updates_status_and_enqueues_worker(
    jobs_routes_with_runner_mock,
    fake_cursor,
    sample_video_plan,
    test_store,
):
    # Given
    job = Job(status=JobStatus.PLANNED)
    test_store["jobs"][job.job_id] = job
    test_store["plans"][job.job_id] = Plan(
        job_id=job.job_id, plan=sample_video_plan, approved=False
    )

    # When
    response = jobs_routes_with_runner_mock.approve_plan(
        request=object(), job_id=job.job_id, approved=True, redis_client=object(), cursor=fake_cursor
    )

    # Then
    assert response.job.status == JobStatus.APPROVED
    assert test_store["jobs"][job.job_id].status == JobStatus.APPROVED
    assert test_store["plans"][job.job_id].approved is True
    assert len(test_store["worker_runner_calls"]) == 1
    runner_call = test_store["worker_runner_calls"][0]
    assert runner_call.job.status == JobStatus.APPROVED
    assert len(runner_call.plan.scenes) == len(sample_video_plan.scenes)


def test_approve_plan_with_false_cancels_job_without_enqueuing_worker(
    jobs_routes_with_runner_mock,
    fake_cursor,
    sample_video_plan,
    test_store,
):
    # Given
    job = Job(status=JobStatus.PLANNED)
    test_store["jobs"][job.job_id] = job
    test_store["plans"][job.job_id] = Plan(
        job_id=job.job_id, plan=sample_video_plan, approved=False
    )

    # When
    response = jobs_routes_with_runner_mock.approve_plan(
        request=object(), job_id=job.job_id, approved=False, redis_client=object(), cursor=fake_cursor
    )

    # Then
    assert response.job.status == JobStatus.CANCELLED
    assert test_store["jobs"][job.job_id].status == JobStatus.CANCELLED
    assert test_store["worker_runner_calls"] == []


def test_approve_plan_raises_409_when_job_is_not_in_planned_state(
    jobs_routes_with_runner_mock,
    fake_cursor,
    test_store,
):
    # Given
    job = Job(status=JobStatus.CREATED)  # CREATED cannot be approved
    test_store["jobs"][job.job_id] = job

    # When / Then
    with pytest.raises(HTTPException) as exc_info:
        jobs_routes_with_runner_mock.approve_plan(
            request=object(), job_id=job.job_id, approved=True, redis_client=object(), cursor=fake_cursor
        )

    assert exc_info.value.status_code == 409
    assert test_store["jobs"][job.job_id].status == JobStatus.CREATED
    assert test_store["worker_runner_calls"] == []
