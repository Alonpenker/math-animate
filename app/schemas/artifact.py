from enum import Enum
from pydantic import BaseModel, Field


class ArtifactType(Enum):
    MP4 = "mp4"
    JSON = "json"
    ZIP = "zip"
    LOG = "log"
    METADATA = "metadata"


class Artifact(BaseModel):
    artifact_type: ArtifactType = Field(..., alias="artifcat_type")
    path: str
    size: int = Field(..., ge=0)
    sha256: str
