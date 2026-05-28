from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from schemas import VideoPlan


class NodeName(StrEnum):
    GENERATE_PLAN = "generate_plan"
    LOAD_STATIC_KNOWLEDGE = "load_static_knowledge"
    GENERATE_CODE = "generate_code"
    VERIFY = "verify"
    FIX_CODE = "fix_code"
    RENDER = "render"
    FAIL = "fail"


@dataclass(frozen=True)
class VerificationResult:
    failure: str = ""
    fixable: bool = True

    @property
    def passed(self) -> bool:
        return not self.failure


class WorkflowState(TypedDict):
    request_text: str
    plan: VideoPlan | None
    messages: Annotated[list[BaseMessage], add_messages]
    code: str
    verification: VerificationResult
    fix_attempt: int
    rendered_files: list[str]


def initial_state(request_text: str) -> WorkflowState:
    return {
        "request_text": request_text,
        "plan": None,
        "messages": [],
        "code": "",
        "verification": VerificationResult(),
        "fix_attempt": 0,
        "rendered_files": [],
    }
