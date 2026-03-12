from typing import List

from pydantic import BaseModel, Field

class UserRequest(BaseModel):
    topic: str
    misconceptions: List[str]
    constraints: List[str]
    examples: List[str]
    number_of_scenes: int = Field(..., ge=1, le=3)
