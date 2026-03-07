from pydantic import BaseModel
from typing import Literal, List

from app.configs.llm_settings import LLM_EMBEDDING_DIMENSIONS

ColumnType = Literal[
    "UUID",
    "TEXT",
    "TEXT[]",
    "JSONB",
    "BOOLEAN",
    "INTEGER",
    "DATE",
    "TIMESTAMP",
    "TIMESTAMPTZ",
    f"VECTOR({LLM_EMBEDDING_DIMENSIONS})",
]

class DBColumn(BaseModel):
    name: str
    type: ColumnType
    attributes: List[str]
    
    @property
    def sql_type(self) -> str:
        parts = [self.type, *self.attributes]
        return " ".join(parts)