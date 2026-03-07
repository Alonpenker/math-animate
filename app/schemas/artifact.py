from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID

from app.schemas.db_column import DBColumn
from app.schemas.schema import Schema
from pathlib import Path


class ArtifactType(Enum):
    MP4 = "mp4"
    JSON = "json"
    ZIP = "zip"
    TXT = "txt"
    LOG = "log"
    METADATA = "metadata"
    PYTHON_FILE = "py"

    @property
    def content_type(self) -> str:
        _content_type_map = {
            ArtifactType.MP4: "video/mp4",
            ArtifactType.PYTHON_FILE: "text/x-python",
            ArtifactType.JSON: "application/json",
            ArtifactType.TXT: "text/plain",
            ArtifactType.LOG: "text/plain",
            ArtifactType.ZIP: "application/zip",
            ArtifactType.METADATA: "application/octet-stream",
        }
        return _content_type_map.get(self, "application/octet-stream")

    @classmethod
    def from_path(cls, path: Path):
        suffix = path.suffix.lower().lstrip('.')

        for artifact_type in cls:
            if artifact_type.value == suffix:
                return artifact_type
        raise ValueError(f"No ArtifactType found for extension: {suffix}")

class Artifact(BaseModel):
    artifact_id: UUID
    job_id: UUID
    artifact_type: ArtifactType = Field(..., alias="artifact_type")
    path: str
    size: int = Field(..., ge=0)
    sha256: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ArtifactResponse(BaseModel):
    artifact_id: UUID
    job_id: UUID
    artifact_type: ArtifactType
    name: str
    size: int
    sha256: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ArtifactSchema(Schema):
    ARTIFACT_ID = DBColumn(name="artifact_id", type="UUID", attributes=["PRIMARY KEY"])
    JOB_ID = DBColumn(name="job_id", type="UUID", attributes=["NOT NULL"])
    ARTIFACT_TYPE = DBColumn(name="artifact_type", type="TEXT", attributes=["NOT NULL"])
    PATH = DBColumn(name="path", type="TEXT", attributes=["NOT NULL"])
    SIZE = DBColumn(name="size", type="INTEGER", attributes=["NOT NULL"])
    SHA256 = DBColumn(name="sha256", type="TEXT", attributes=["NOT NULL"])
