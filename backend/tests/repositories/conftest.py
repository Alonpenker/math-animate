from typing import Any

class FakeSqlCursor:

    def __init__(self, rows: list[dict[str, Any]] | None = None, rowcount: int = 0):
        self.queries: list[tuple[str, Any]] = []
        self.rows: list[dict[str, Any]] = list(rows or [])
        self.rowcount: int = rowcount

    def execute(self, query: str, params=None) -> None:
        self.queries.append((query, params))

    def fetchone(self) -> dict[str, Any] | None:
        return self.rows[0] if self.rows else None

    def fetchall(self) -> list[dict[str, Any]]:
        return list(self.rows)

class FakeRedis:

    def __init__(self):
        self._store: dict[str, tuple[bytes, int | None]] = {}

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        raw = value.encode() if isinstance(value, str) else value
        self._store[key] = (raw, ex)

    def get(self, key: str) -> bytes | None:
        entry = self._store.get(key)
        return entry[0] if entry is not None else None

    def get_ttl(self, key: str) -> int | None:
        entry = self._store.get(key)
        return entry[1] if entry is not None else None
