from typing import Annotated, List

from pydantic import BaseModel, Field

BoundedStr = Annotated[str, Field(max_length=150)]
TopicStr = Annotated[str, Field(max_length=70)]
BoundedStrList = Annotated[List[BoundedStr], Field(max_length=5)]

class UserRequest(BaseModel):
    topic: TopicStr
    misconceptions: BoundedStrList
    constraints: BoundedStrList
    examples: BoundedStrList
    number_of_scenes: int = Field(..., ge=1, le=3)

    def __str__(self) -> str:
        return (
            f"Topic: {self.topic}\n"
            f"Misconceptions: {', '.join(self.misconceptions)}\n"
            f"Constraints: {', '.join(self.constraints)}\n"
            f"Number of scenes: {self.number_of_scenes}"
        )
