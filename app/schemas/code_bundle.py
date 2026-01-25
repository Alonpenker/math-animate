from enum import Enum
from typing import List

from pydantic import BaseModel

class RenderQuality(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class CodeBundle(BaseModel):
    files: List[str]
    entry_scene: str
    render_config: RenderQuality
