from typing import List, Optional
from uuid import UUID

from app.schemas.artifact import Artifact, ArtifactType, ArtifactSchema
from app.repositories.repository import Repository


class ArtifactsRepository(Repository):

    TABLE_NAME = 'artifacts'
    SCHEMA = ArtifactSchema
    PRIMARY_KEY = "artifact_id"

    @classmethod
    def _row_to_artifact(cls, row) -> Artifact:
        return Artifact(
            artifact_id=row[ArtifactSchema.ARTIFACT_ID.name],
            job_id=row[ArtifactSchema.JOB_ID.name],
            artifact_type=ArtifactType(row[ArtifactSchema.ARTIFACT_TYPE.name]),
            path=row[ArtifactSchema.PATH.name],
            size=row[ArtifactSchema.SIZE.name],
            sha256=row[ArtifactSchema.SHA256.name],
            created_at=row[ArtifactSchema.CREATED_AT.name],
            updated_at=row[ArtifactSchema.UPDATED_AT.name],
        )

    @classmethod
    def create_artifact(cls, cursor, artifact: Artifact) -> None:
        cursor.execute(
            cls.insert(),
            (
                str(artifact.artifact_id),
                str(artifact.job_id),
                artifact.artifact_type.value,
                artifact.path,
                artifact.size,
                artifact.sha256,
            ),
        )

    @classmethod
    def get_artifacts(cls, cursor, job_id: UUID) -> List[Artifact]:
        cursor.execute(
            cls.get_all_by_job(),
            (str(job_id),),
        )
        rows = cursor.fetchall()
        return [cls._row_to_artifact(row) for row in rows]

    @classmethod
    def get_artifact_by_id(cls, cursor, artifact_id: UUID) -> Artifact | None:
        cursor.execute(cls.get(), (str(artifact_id),))
        row = cursor.fetchone()
        if row is None:
            return None
        return cls._row_to_artifact(row)

    @classmethod
    def get_all_artifacts(
        cls,
        cursor,
        artifact_type: Optional[ArtifactType] = None,
        job_id: Optional[UUID] = None,
    ) -> List[Artifact]:
        conditions = []
        params = []
        if artifact_type is not None:
            conditions.append(f"{ArtifactSchema.ARTIFACT_TYPE.name} = %s")
            params.append(artifact_type.value)
        if job_id is not None:
            conditions.append(f"{ArtifactSchema.JOB_ID.name} = %s")
            params.append(str(job_id))

        query = f"SELECT * FROM {cls.TABLE_NAME}"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += f" ORDER BY {ArtifactSchema.CREATED_AT.name} DESC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [cls._row_to_artifact(row) for row in rows]

    @classmethod
    def delete_artifact(cls, cursor, artifact_id: UUID) -> bool:
        cursor.execute(cls.delete(), (str(artifact_id),))
        return cursor.rowcount > 0
