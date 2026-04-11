from pydantic import BaseModel, Field

class ScenePlan(BaseModel):
    learning_objective: str
    visual_storyboard: str
    voice_notes: str
    scene_number: int = Field(..., ge=-1, le=3)