"""
Shared fixtures for repository tests.

Provides FakeSqlCursor (a psycopg2 DictCursor double) and FakeRedis
so repository tests run without any real database or Redis connection.
"""
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# SQL cursor double
# ─────────────────────────────────────────────────────────────────────────────

class FakeSqlCursor:
    """
    Minimal psycopg2 DictCursor double.

    Pre-populate `rows` for fetchone / fetchall returns.
    Set `rowcount` before calling a repository method that checks affected rows.
    All executed (query, params) pairs are recorded in `queries`.
    """

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


# ─────────────────────────────────────────────────────────────────────────────
# Redis double
# ─────────────────────────────────────────────────────────────────────────────

class FakeRedis:
    """
    Minimal Redis double that supports get / set (with optional TTL).
    Records the TTL passed to `set` so tests can assert on expiry behaviour.
    """

    def __init__(self):
        self._store: dict[str, tuple[bytes, int | None]] = {}

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        raw = value.encode() if isinstance(value, str) else value
        self._store[key] = (raw, ex)

    def get(self, key: str) -> bytes | None:
        entry = self._store.get(key)
        return entry[0] if entry is not None else None

    def get_ttl(self, key: str) -> int | None:
        """Return the TTL supplied to `set`, or None if key is unknown."""
        entry = self._store.get(key)
        return entry[1] if entry is not None else None
