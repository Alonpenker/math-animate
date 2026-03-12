from enum import Enum
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.db_column import DBColumn
from app.schemas.schema import Schema
from app.configs.llm_settings import LLM_EMBEDDING_DIMENSIONS


class KnowledgeType(str, Enum):
    PLAN = "plan"
    CODE = "code"

class KnowledgeDocument(BaseModel):
    document_id: UUID
    content: str
    doc_type: KnowledgeType
    title: str

class KnowledgeDocumentCreate(BaseModel):
    content: str = Field(..., min_length=1)
    doc_type: KnowledgeType
    title: str = Field("", max_length=255)

class KnowledgeDocumentResponse(BaseModel):
    document: KnowledgeDocument


class KnowledgeDocumentsListResponse(BaseModel):
    documents: List[KnowledgeDocument]


class SeedKnowledgeResponse(BaseModel):
    inserted: int
    skipped: int


class KnowledgeDocumentSchema(Schema):
    DOCUMENT_ID = DBColumn(name="document_id", type="UUID", attributes=["PRIMARY KEY"])
    CONTENT = DBColumn(name="content", type="TEXT", attributes=["NOT NULL"])
    DOC_TYPE = DBColumn(name="doc_type", type="TEXT", attributes=["NOT NULL"])
    TITLE = DBColumn(name="title", type="TEXT", attributes=["NOT NULL", "DEFAULT ''"])
    EMBEDDING = DBColumn(name="embedding", type=f"VECTOR({LLM_EMBEDDING_DIMENSIONS})", attributes=["NOT NULL"])
