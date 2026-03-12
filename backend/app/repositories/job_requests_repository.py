from typing import List, Optional
from uuid import UUID

from app.domain.job_state import JobStatus
from app.repositories.repository import Repository
from app.schemas.job_request import JobRequestSchema, JobListItem
from app.schemas.schema import Schema
from app.schemas.user_request import UserRequest


class JobRequestsRepository(Repository):

    TABLE_NAME = "job_requests"
    SCHEMA = JobRequestSchema
    PRIMARY_KEY = "job_id"

    @classmethod
    def create(cls, cursor, job_id: UUID, user_request: UserRequest, status: JobStatus) -> None:
        cursor.execute(
            cls.insert(),
            (
                str(job_id),
                user_request.topic,
                user_request.misconceptions,
                user_request.constraints,
                user_request.examples,
                user_request.number_of_scenes,
                status.value,
            ),
        )

    @classmethod
    def update_status(cls, cursor, job_id: UUID, status: JobStatus) -> None:
        cursor.execute(
            cls.modify(cls.SCHEMA.STATUS.name),
            (status.value, str(job_id)),
        )

    @classmethod
    def get_job_requests(
        cls,
        cursor,
        page: int = 1,
        page_size: int = 20,
        topic: Optional[str] = None,
        job_id: Optional[UUID] = None,
        status: Optional[str] = None,
    ) -> tuple[List[JobListItem], int]:
        conditions: list[str] = []
        params: list = []

        if topic is not None:
            conditions.append(f"{JobRequestSchema.TOPIC.name} ILIKE %s")
            params.append(f"%{topic}%")
        if job_id is not None:
            conditions.append(f"{JobRequestSchema.JOB_ID.name} = %s")
            params.append(str(job_id))
        if status is not None:
            conditions.append(f"{JobRequestSchema.STATUS.name} = %s")
            params.append(status)

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        count_query = f"SELECT COUNT(*) AS total FROM {cls.TABLE_NAME} {where_clause}"
        cursor.execute(count_query, tuple(params))
        total = cursor.fetchone()["total"]

        offset = (page - 1) * page_size
        data_query = (
            f"SELECT {JobRequestSchema.JOB_ID.name}, {JobRequestSchema.TOPIC.name}, "
            f"{JobRequestSchema.MISCONCEPTIONS.name}, {JobRequestSchema.CONSTRAINTS.name}, "
            f"{JobRequestSchema.EXAMPLES.name}, {JobRequestSchema.NUMBER_OF_SCENES.name}, "
            f"{JobRequestSchema.STATUS.name}, {Schema.CREATED_AT.name}, {Schema.UPDATED_AT.name} "
            f"FROM {cls.TABLE_NAME} {where_clause} "
            f"ORDER BY {Schema.CREATED_AT.name} DESC LIMIT %s OFFSET %s"
        )
        cursor.execute(data_query, (*params, page_size, offset))
        rows = cursor.fetchall()

        items = [
            JobListItem(
                job_id=row[JobRequestSchema.JOB_ID.name],
                topic=row[JobRequestSchema.TOPIC.name],
                misconceptions=row[JobRequestSchema.MISCONCEPTIONS.name],
                constraints=row[JobRequestSchema.CONSTRAINTS.name],
                examples=row[JobRequestSchema.EXAMPLES.name],
                number_of_scenes=row[JobRequestSchema.NUMBER_OF_SCENES.name],
                status=JobStatus(row[JobRequestSchema.STATUS.name]),
                created_at=row[Schema.CREATED_AT.name],
                updated_at=row[Schema.UPDATED_AT.name],
            )
            for row in rows
        ]

        return items, total
