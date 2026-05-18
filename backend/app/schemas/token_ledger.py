from enum import StrEnum

from app.schemas.db_column import DBColumn
from app.schemas.schema import Schema

class State(StrEnum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"

class TokenLedgerSchema(Schema):
    CALL_ID = DBColumn(name="call_id", type="UUID", attributes=["PRIMARY KEY"])
    DAY = DBColumn(name="day", type="DATE", attributes=["NOT NULL"])
    JOB_ID = DBColumn(name="job_id", type="UUID", attributes=["NOT NULL"])
    STAGE = DBColumn(name="stage", type="TEXT", attributes=["NOT NULL"])
    PROVIDER = DBColumn(name="provider", type="TEXT", attributes=["NOT NULL"])
    MODEL = DBColumn(name="model", type="TEXT", attributes=["NOT NULL"])
    CALL_TYPE = DBColumn(name="call_type", type="TEXT", attributes=["NOT NULL", "DEFAULT 'unknown'"])
    INPUT_TOKENS = DBColumn(name="input_tokens", type="INTEGER", attributes=["NOT NULL", "DEFAULT 0"])
    OUTPUT_TOKENS = DBColumn(name="output_tokens", type="INTEGER", attributes=["NOT NULL", "DEFAULT 0"])
    REASONING_TOKENS = DBColumn(name="reasoning_tokens", type="INTEGER", attributes=["NOT NULL", "DEFAULT 0"])
    RESERVED_TOKENS = DBColumn(name="reserved_tokens", type="INTEGER", attributes=["NOT NULL"])
    CONSUMED_TOKENS = DBColumn(name="consumed_tokens", type="INTEGER", attributes=["NOT NULL", "DEFAULT 0"])
    STATE = DBColumn(name="state", type="TEXT", attributes=["NOT NULL", f"DEFAULT '{State.ACTIVE}'"])
