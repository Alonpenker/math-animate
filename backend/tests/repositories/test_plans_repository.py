"""
PlansRepository tests.

Uses FakeSqlCursor to verify SQL interactions and domain object construction
without any real database connection.
"""
from uuid import uuid4

from app.repositories.plans_repository import PlansRepository
from app.schemas.scene_plan import ScenePlan
from app.schemas.video_plan import VideoPlan

from tests.repositories.conftest import FakeSqlCursor


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_video_plan() -> VideoPlan:
    return VideoPlan(
        scenes=[
            ScenePlan(
                learning_objective="Identify the variable.",
                visual_storyboard="Highlight x in x + 3 = 7.",
                voice_notes="The variable is what we solve for.",
                scene_number=1,
            )
        ]
    )


def _plan_row(job_id, plan: VideoPlan, approved: bool = False) -> dict:
    return {
        "job_id": str(job_id),
        "plan": plan.model_dump_json(),
        "approved": approved,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PlansRepository.create_plan
# ─────────────────────────────────────────────────────────────────────────────

def test_create_plan_executes_insert_with_job_id_and_json_plan():
    # Given
    cursor = FakeSqlCursor()
    job_id = uuid4()
    plan = _make_video_plan()

    # When
    PlansRepository.create_plan(cursor, job_id, plan)

    # Then
    assert len(cursor.queries) == 1
    _, params = cursor.queries[0]
    assert str(job_id) in params
    assert plan.model_dump_json() in params


# ─────────────────────────────────────────────────────────────────────────────
# PlansRepository.get_plan
# ─────────────────────────────────────────────────────────────────────────────

def test_get_plan_returns_plan_with_correct_data_when_row_exists():
    # Given
    job_id = uuid4()
    plan = _make_video_plan()
    cursor = FakeSqlCursor(rows=[_plan_row(job_id, plan, approved=False)])

    # When
    result = PlansRepository.get_plan(cursor, job_id)

    # Then
    assert result is not None
    assert str(result.job_id) == str(job_id)
    assert result.approved is False
    assert len(result.plan.scenes) == 1


def test_get_plan_returns_none_when_no_row_found():
    # Given
    cursor = FakeSqlCursor(rows=[])

    # When
    result = PlansRepository.get_plan(cursor, uuid4())

    # Then
    assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# PlansRepository.approve_plan
# ─────────────────────────────────────────────────────────────────────────────

def test_approve_plan_executes_update_and_returns_updated_plan():
    # Given
    job_id = uuid4()
    plan = _make_video_plan()
    # approve_plan calls get_plan internally after the UPDATE,
    # so the cursor must return the plan row on fetchone().
    cursor = FakeSqlCursor(rows=[_plan_row(job_id, plan, approved=True)])

    # When
    result = PlansRepository.approve_plan(cursor, job_id, approved=True)

    # Then
    # Two execute calls: one UPDATE + one SELECT from get_plan
    assert len(cursor.queries) == 2
    assert result is not None
    assert result.approved is True
