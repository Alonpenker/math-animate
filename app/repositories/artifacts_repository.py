from typing import List
from uuid import UUID

from app.schemas.artifact import Artifact, ArtifactType, ArtifactSchema
from app.repositories.repository import Repository


class ArtifactsRepository(Repository):

    TABLE_NAME = 'artifacts'
    SCHEMA = ArtifactSchema
    PRIMARY_KEY = "artifact_id"

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
        return [
            Artifact(
                artifact_id=row[ArtifactSchema.ARTIFACT_ID.name],
                job_id=row[ArtifactSchema.JOB_ID.name],
                artifact_type=ArtifactType(row[ArtifactSchema.ARTIFACT_TYPE.name]),
                path=row[ArtifactSchema.PATH.name],
                size=row[ArtifactSchema.SIZE.name],
                sha256=row[ArtifactSchema.SHA256.name],
            )
            for row in rows
        ]

    @classmethod
    def get_artifact_by_id(cls, cursor, artifact_id: UUID) -> Artifact | None:
        cursor.execute(cls.get(), (str(artifact_id),))
        row = cursor.fetchone()
        if row is None:
            return None
        return Artifact(
            artifact_id=row[ArtifactSchema.ARTIFACT_ID.name],
            job_id=row[ArtifactSchema.JOB_ID.name],
            artifact_type=ArtifactType(row[ArtifactSchema.ARTIFACT_TYPE.name]),
            path=row[ArtifactSchema.PATH.name],
            size=row[ArtifactSchema.SIZE.name],
            sha256=row[ArtifactSchema.SHA256.name],
        )
