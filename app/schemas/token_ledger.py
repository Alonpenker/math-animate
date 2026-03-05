from enum import StrEnum

from app.schemas.db_column import DBColumn
from app.schemas.schema import Schema

class State(StrEnum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"

class TokenLedgerSchema(Schema):
    CALL_ID = DBColumn(name="call_id", type="UUID", attributes=["PRIMARY KEY"])
    DAY = DBColumn(name="day", type="DATE", attributes=["NOT NULL"])
    JOB_ID = DBColumn(name="job_id", type="UUID", attributes=["NOT NULL"])
    STAGE = DBColumn(name="stage", type="TEXT", attributes=["NOT NULL"])
    PROVIDER = DBColumn(name="provider", type="TEXT", attributes=["NOT NULL"])
    MODEL = DBColumn(name="model", type="TEXT", attributes=["NOT NULL"])
    RESERVED_TOKENS = DBColumn(name="reserved_tokens", type="INTEGER", attributes=["NOT NULL"])
    CONSUMED_TOKENS = DBColumn(name="consumed_tokens", type="INTEGER", attributes=["NOT NULL", "DEFAULT 0"])
    STATE = DBColumn(name="state", type="TEXT", attributes=["NOT NULL", f"DEFAULT '{State.ACTIVE}'"])
    CREATED_AT = DBColumn(name="created_at", type="TIMESTAMPTZ", attributes=["NOT NULL", "DEFAULT NOW()"])
    UPDATED_AT = DBColumn(name="updated_at", type="TIMESTAMPTZ", attributes=["NOT NULL", "DEFAULT NOW()"])
