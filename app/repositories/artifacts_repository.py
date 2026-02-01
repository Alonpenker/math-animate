from typing import List
from uuid import UUID

from app.schemas.artifact import Artifact, ArtifactType
from app.repositories.repository import Repository


class ArtifactsRepository(Repository):

    TABLE_NAME = 'artifacts'
    COLUMNS = [
        ("job_id","UUID PRIMARY KEY"),
        ("artifact_type","TEXT"),
        ("path","TEXT"),
        ("size","INTEGER"),
        ("sha256","TEXT"),
    ]
    PRIMARY_KEY = 'job_id'

    @classmethod
    def create_artifact(cls, cursor, artifact: Artifact) -> None:
        cursor.execute(
            cls.insert(),
            (
                str(artifact.job_id),
                artifact.artifact_type.value,
                artifact.path,
                artifact.size,
                artifact.sha256,
            ),
        )

    @classmethod
    def get_artifacts(cls, cursor, job_id: UUID) -> List[Artifact]:
        cursor.execute(cls.get_all_by_key(), (str(job_id),))
        rows = cursor.fetchall()
        return [
            Artifact(
                job_id=job_id,
                artifact_type=ArtifactType(row[1]),
                path=row[2],
                size=row[3],
                sha256=row[4],
            )
            for row in rows
        ]
