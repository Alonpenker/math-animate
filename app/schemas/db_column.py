from pydantic import BaseModel
from typing import Literal, List

ColumnType = Literal[
    "UUID",
    "TEXT",
    "JSONB",
    "BOOLEAN",
    "INTEGER",
    "TIMESTAMP",
]

class DBColumn(BaseModel):
    name: str
    type: ColumnType
    attributes: List[str]
    
    @property
    def sql_type(self) -> str:
        parts = [self.type, *self.attributes]
        return " ".join(parts)