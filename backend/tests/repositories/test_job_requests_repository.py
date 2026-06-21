from uuid import uuid4

from app.domain.job_state import JobStatus
from app.repositories.job_requests_repository import JobRequestsRepository

from tests.repositories.conftest import FakeSqlCursor


def test_get_status_returns_persisted_job_status():
    job_id = uuid4()
    cursor = FakeSqlCursor(rows=[{"status": "RENDERED"}])

    result = JobRequestsRepository.get_status(cursor, job_id)

    assert result == JobStatus.RENDERED
    assert cursor.queries[-1][1] == (str(job_id),)


def test_get_status_returns_none_when_job_does_not_exist():
    cursor = FakeSqlCursor()

    result = JobRequestsRepository.get_status(cursor, uuid4())

    assert result is None
