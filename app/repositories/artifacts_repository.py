from typing import Optional, List, Dict
from uuid import UUID

from app.dependencies.db import get_cursor
from app.schemas.artifact import Artifact


class ArtifactsRepository:
    
    def create_artifact(
        self, job_id: UUID, artifact: Artifact
    ) -> None:
        pass

    def get_artifacts(self, job_id: UUID) -> Optional[List[Dict]]:
        pass

