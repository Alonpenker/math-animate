from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID


class ArtifactType(Enum):
    MP4 = "mp4"
    JSON = "json"
    ZIP = "zip"
    TXT = "txt"
    LOG = "log"
    METADATA = "metadata"
    PYTHON_FILE = "py"
    
class Artifact(BaseModel):
    job_id: UUID
    artifact_type: ArtifactType = Field(..., alias="artifact_type")
    path: str
    size: int = Field(..., ge=0)
    sha256: str
