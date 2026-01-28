from typing import Optional, List, Dict
from uuid import UUID

from app.schemas.artifact import Artifact


class ArtifactsRepository:
    
    @staticmethod
    def _verify_table(cursor) -> None:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS artifacts (job_id TEXT, artifact_type TEXT, path TEXT, size INTEGER, sha256 TEXT)"
        )
        
    @staticmethod
    def create_artifact(
        cursor, artifact: Artifact
    ) -> None:
        ArtifactsRepository._verify_table(cursor)
        cursor.execute(
            "INSERT INTO artifacts (job_id, artifact_type, path, size, sha256) VALUES (%s, %s, %s, %s, %s)",
            (
                str(artifact.job_id),
                artifact.artifact_type.value,
                artifact.path,
                artifact.size,
                artifact.sha256,
            ),
        )

    @staticmethod
    def get_artifacts(cursor, job_id: UUID) -> Optional[List[Dict]]:
        ArtifactsRepository._verify_table(cursor)
        cursor.execute(
            "SELECT artifact_type, path, size, sha256 FROM artifacts WHERE job_id = %s",
            (str(job_id),),
        )
        rows = cursor.fetchall()
        if not rows:
            return None
        return [
            {"artifact_type": row[0], "path": row[1], "size": row[2], "sha256": row[3]}
            for row in rows
        ]
