from typing import List
from uuid import UUID

from app.schemas.artifact import Artifact, ArtifactType
from app.repositories.repository import Repository


class ArtifactsRepository(Repository):

    TABLE_NAME = 'artifacts'
    COLUMNS = [
        ("artifact_id","UUID PRIMARY KEY"),
        ("job_id","UUID"),
        ("artifact_type","TEXT"),
        ("path","TEXT"),
        ("size","INTEGER"),
        ("sha256","TEXT"),
    ]
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
                artifact_id=row[0],
                job_id=row[1],
                artifact_type=ArtifactType(row[2]),
                path=row[3],
                size=row[4],
                sha256=row[5],
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
            artifact_id=row[0],
            job_id=row[1],
            artifact_type=ArtifactType(row[2]),
            path=row[3],
            size=row[4],
            sha256=row[5],
        )
