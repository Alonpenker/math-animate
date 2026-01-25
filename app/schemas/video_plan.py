from typing import List
from pydantic import BaseModel

from schemas.scene_plan import ScenePlan

class VideoPlan(BaseModel):
    scenes: List[ScenePlan]
