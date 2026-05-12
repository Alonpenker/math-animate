from enum import Enum
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.configs.llm_settings import LLM_EMBEDDING_DIMENSIONS
from app.schemas.db_column import DBColumn
from app.schemas.schema import Schema


class KnowledgeType(str, Enum):
    SKILL = "skill"
    RULE = "rule"
    TEMPLATE = "template"
    EXAMPLE = "example"


PriorityType = Literal["core", "recommended", "optional"]


class KnowledgeDocument(BaseModel):
    document_id: UUID
    doc_type: KnowledgeType
    title: str
    category: str = ""
    priority: PriorityType = "optional"
    tags: list[str] = Field(default_factory=list)

    def to_metadata(self) -> str:
        tags = ", ".join(self.tags) if self.tags else "none"
        return (
            f"- {self.title} "
            f"(type={self.doc_type.value}, category={self.category}, "
            f"priority={self.priority}, tags={tags})"
        )


class KnowledgeDocumentSeed(KnowledgeDocument):
    path: str


@dataclass
class CandidateResult:
    candidate_rules: list[KnowledgeDocument]
    candidate_templates: list[KnowledgeDocument]
    candidate_examples: list[KnowledgeDocument]

    @property
    def all_candidates(self) -> list[KnowledgeDocument]:
        return self.candidate_rules + self.candidate_templates + self.candidate_examples


class KnowledgeDocumentResponse(BaseModel):
    document: KnowledgeDocument


class KnowledgeDocumentsListResponse(BaseModel):
    documents: list[KnowledgeDocument]


class KnowledgeDocumentSchema(Schema):
    DOCUMENT_ID = DBColumn(name="document_id", type="UUID", attributes=["PRIMARY KEY"])
    DOC_TYPE = DBColumn(name="doc_type", type="TEXT", attributes=["NOT NULL"])
    PRIORITY = DBColumn(name="priority", type="TEXT", attributes=["NOT NULL", "DEFAULT 'optional'"])
    TITLE = DBColumn(name="title", type="TEXT", attributes=["NOT NULL", "DEFAULT ''"])
    CATEGORY = DBColumn(name="category", type="TEXT", attributes=["NOT NULL", "DEFAULT ''"])
    EMBEDDING = DBColumn(name="embedding", type=f"VECTOR({LLM_EMBEDDING_DIMENSIONS})", attributes=["NOT NULL"])
    TAGS = DBColumn(name="tags", type="TEXT[]", attributes=["NOT NULL", "DEFAULT '{}'"])
