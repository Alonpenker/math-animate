from typing import Optional

from pydantic import BaseModel, Field

class ScenePlan(BaseModel):
    learning_objective: str
    visual_storyboard: str
    voice_notes: str
    duration_seconds: int = Field(..., ge=1)
    template_hints: Optional[str] = None
