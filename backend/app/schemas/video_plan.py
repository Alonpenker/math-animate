from typing import List
from pydantic import BaseModel

from app.schemas.scene_plan import ScenePlan

class VideoPlan(BaseModel):
    scenes: List[ScenePlan]

    def to_prompt_text(self) -> str:
        return self.model_dump_json(indent=2)
