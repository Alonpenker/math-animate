from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from schemas import CodePlan, KnowledgeDocumentSeed, VideoPlan


class NodeName(StrEnum):
    GENERATE_PLAN = "generate_plan"
    LOAD_STATIC_KNOWLEDGE = "load_static_knowledge"
    GENERATE_CODE_PLAN = "generate_code_plan"
    GENERATE_CODE = "generate_code"
    CODE_QA = "code_qa"
    VERIFY = "verify"
    FIX_CODE = "fix_code"
    RENDER = "render"
    FAIL = "fail"


FIX_RETRY_PATH: tuple[NodeName, ...] = (
    NodeName.FIX_CODE,
    NodeName.VERIFY,
)

INITIAL_ATTEMPT = 1


def workflow_recursion_limit(max_attempts: int) -> int:
    """Return the LangGraph node-visit budget implied by the workflow paths."""
    retry_count = max(0, max_attempts - INITIAL_ATTEMPT)
    return len(tuple(NodeName)) + retry_count * len(FIX_RETRY_PATH)


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
    code_plan: CodePlan | None
    referenced_templates: list[KnowledgeDocumentSeed]
    messages: Annotated[list[BaseMessage], add_messages]
    code: str
    verification: VerificationResult
    attempt: int
    code_qa_completed: bool
    rendered_files: list[str]


def initial_state(request_text: str) -> WorkflowState:
    return {
        "request_text": request_text,
        "plan": None,
        "code_plan": None,
        "referenced_templates": [],
        "messages": [],
        "code": "",
        "verification": VerificationResult(),
        "attempt": INITIAL_ATTEMPT,
        "code_qa_completed": False,
        "rendered_files": [],
    }
