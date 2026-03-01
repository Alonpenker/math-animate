from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.domain.job_state import JobStatus
from app.schemas.jobs import Job
from app.schemas.plan import Plan


def test_create_job_persists_created_and_calls_worker_runner(
    jobs_routes_with_runner_mock,
    fake_cursor,
    sample_user_request,
    test_store,
):
    response = jobs_routes_with_runner_mock.create_job(sample_user_request, cursor=fake_cursor)

    assert response.job.status == JobStatus.CREATED
    assert response.job.job_id in test_store["jobs"]
    assert test_store["jobs"][response.job.job_id].status == JobStatus.CREATED

    assert len(test_store["worker_runner_calls"]) == 1
    runner_request = test_store["worker_runner_calls"][0]
    assert runner_request.job.job_id == response.job.job_id
    assert runner_request.job.status == JobStatus.CREATED
    assert runner_request.user_request.topic == sample_user_request.topic


def test_get_job_status_returns_current_status(
    jobs_routes_with_runner_mock,
    fake_cursor,
    test_store,
):
    job = Job(status=JobStatus.PLANNED)
    test_store["jobs"][job.job_id] = job

    response = jobs_routes_with_runner_mock.get_job_status(job.job_id, cursor=fake_cursor)

    assert response.job.job_id == job.job_id
    assert response.job.status == JobStatus.PLANNED


def test_get_job_status_not_found_returns_404(
    jobs_routes_with_runner_mock,
    fake_cursor,
):
    with pytest.raises(HTTPException) as exc_info:
        jobs_routes_with_runner_mock.get_job_status(uuid4(), cursor=fake_cursor)

    assert exc_info.value.status_code == 404
    assert "Job not found" in exc_info.value.detail


def test_get_plan_returns_existing_plan(
    jobs_routes_with_runner_mock,
    fake_cursor,
    sample_video_plan,
    test_store,
):
    job = Job(status=JobStatus.PLANNED)
    test_store["jobs"][job.job_id] = job
    test_store["plans"][job.job_id] = Plan(
        job_id=job.job_id,
        plan=sample_video_plan,
        approved=False,
    )

    response = jobs_routes_with_runner_mock.get_plan(job.job_id, cursor=fake_cursor)

    assert response.job.job_id == job.job_id
    assert response.job.status == JobStatus.PLANNED
    assert response.data.job_id == job.job_id


def test_get_plan_not_found_returns_404(
    jobs_routes_with_runner_mock,
    fake_cursor,
    test_store,
):
    job = Job(status=JobStatus.PLANNED)
    test_store["jobs"][job.job_id] = job

    with pytest.raises(HTTPException) as exc_info:
        jobs_routes_with_runner_mock.get_plan(job.job_id, cursor=fake_cursor)

    assert exc_info.value.status_code == 404
    assert "Plan not found" in exc_info.value.detail


def test_approve_plan_true_updates_status_and_calls_worker_runner(
    jobs_routes_with_runner_mock,
    fake_cursor,
    sample_video_plan,
    test_store,
):
    job = Job(status=JobStatus.PLANNED)
    test_store["jobs"][job.job_id] = job
    test_store["plans"][job.job_id] = Plan(
        job_id=job.job_id,
        plan=sample_video_plan,
        approved=False,
    )

    response = jobs_routes_with_runner_mock.approve_plan(
        job.job_id, approved=True, cursor=fake_cursor
    )

    assert response.job.status == JobStatus.APPROVED
    assert test_store["jobs"][job.job_id].status == JobStatus.APPROVED
    assert test_store["plans"][job.job_id].approved is True

    assert len(test_store["worker_runner_calls"]) == 1
    runner_request = test_store["worker_runner_calls"][0]
    assert runner_request.job.job_id == job.job_id
    assert runner_request.job.status == JobStatus.APPROVED
    assert len(runner_request.plan.scenes) == len(sample_video_plan.scenes)


def test_approve_plan_false_cancels_without_worker_runner(
    jobs_routes_with_runner_mock,
    fake_cursor,
    sample_video_plan,
    test_store,
):
    job = Job(status=JobStatus.PLANNED)
    test_store["jobs"][job.job_id] = job
    test_store["plans"][job.job_id] = Plan(
        job_id=job.job_id,
        plan=sample_video_plan,
        approved=False,
    )

    response = jobs_routes_with_runner_mock.approve_plan(
        job.job_id, approved=False, cursor=fake_cursor
    )

    assert response.job.status == JobStatus.CANCELLED
    assert test_store["jobs"][job.job_id].status == JobStatus.CANCELLED
    assert test_store["worker_runner_calls"] == []


def test_approve_plan_invalid_state_returns_409(
    jobs_routes_with_runner_mock,
    fake_cursor,
    test_store,
):
    job = Job(status=JobStatus.CREATED)
    test_store["jobs"][job.job_id] = job

    with pytest.raises(HTTPException) as exc_info:
        jobs_routes_with_runner_mock.approve_plan(job.job_id, approved=True, cursor=fake_cursor)

    assert exc_info.value.status_code == 409
    assert test_store["jobs"][job.job_id].status == JobStatus.CREATED
    assert test_store["worker_runner_calls"] == []


