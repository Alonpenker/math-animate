from typing import Annotated, List

from pydantic import BaseModel, Field

BoundedStr = Annotated[str, Field(max_length=150)]

class UserRequest(BaseModel):
    topic: str
    misconceptions: List[BoundedStr]
    constraints: List[BoundedStr]
    examples: List[BoundedStr]
    number_of_scenes: int = Field(..., ge=1, le=3)
