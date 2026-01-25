from __future__ import annotations

from typing import Protocol


class Planner(Protocol):
    """Planner interface for turning lesson input into a scene plan."""

    # TODO: Decide on plan input/output schemas.
    # Option A: Pydantic models in domain/ for LessonInput and ScenePlan.
    # Option B: Pydantic models in app/schemas/ shared via services layer.

    def plan(self, lesson_input: object) -> object:
        ...
