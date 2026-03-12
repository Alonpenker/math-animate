"""
DB dependency tests.

Verifies get_cursor lifecycle: vector registration, commit/rollback, and
connection pool return on both success and failure paths.
"""
import pytest

from app.dependencies import db as db_module


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

class FakeCursor:
    def __init__(self) -> None:
        self.executed: list[str] = []
        self.closed = False

    def execute(self, query: str) -> None:
        self.executed.append(query)

    def close(self) -> None:
        self.closed = True


class FakeConnection:
    def __init__(self) -> None:
        self.cursor_obj = FakeCursor()
        self.cursor_factories: list[object] = []
        self.commit_calls = 0
        self.rollback_calls = 0

    def cursor(self, cursor_factory=None):
        self.cursor_factories.append(cursor_factory)
        return self.cursor_obj

    def commit(self) -> None:
        self.commit_calls += 1

    def rollback(self) -> None:
        self.rollback_calls += 1


class FakePool:
    def __init__(self, conn: FakeConnection) -> None:
        self._conn = conn
        self.getconn_calls = 0
        self.putconn_calls: list[tuple[FakeConnection, bool]] = []

    def getconn(self) -> FakeConnection:
        self.getconn_calls += 1
        return self._conn

    def putconn(self, conn: FakeConnection, close: bool = False) -> None:
        self.putconn_calls.append((conn, close))


# ─────────────────────────────────────────────────────────────────────────────
# get_cursor — success path
# ─────────────────────────────────────────────────────────────────────────────

def test_get_cursor_registers_vector_commits_and_returns_connection_to_pool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    conn = FakeConnection()
    pool = FakePool(conn)
    register_calls: list[FakeConnection] = []

    monkeypatch.setattr(db_module, "db_pool", pool)
    monkeypatch.setattr(db_module, "register_vector", lambda c: register_calls.append(c))

    # When
    cursor_gen = db_module.get_cursor()
    cursor = next(cursor_gen)
    with pytest.raises(StopIteration):
        next(cursor_gen)

    # Then
    assert cursor is conn.cursor_obj
    assert register_calls == [conn]
    assert conn.commit_calls == 1
    assert conn.rollback_calls == 0
    assert pool.putconn_calls == [(conn, False)]


def test_get_cursor_registers_vector_on_each_successive_checkout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    conn = FakeConnection()
    pool = FakePool(conn)
    register_calls: list[FakeConnection] = []

    monkeypatch.setattr(db_module, "db_pool", pool)
    monkeypatch.setattr(db_module, "register_vector", lambda c: register_calls.append(c))

    # When – two independent get_cursor calls
    first_gen = db_module.get_cursor()
    next(first_gen)
    with pytest.raises(StopIteration):
        next(first_gen)

    second_gen = db_module.get_cursor()
    next(second_gen)
    with pytest.raises(StopIteration):
        next(second_gen)

    # Then
    assert register_calls == [conn, conn]
    assert conn.commit_calls == 2
    assert pool.putconn_calls == [(conn, False), (conn, False)]


# ─────────────────────────────────────────────────────────────────────────────
# get_cursor — failure path
# ─────────────────────────────────────────────────────────────────────────────

def test_get_cursor_returns_connection_to_pool_with_close_flag_when_registration_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    conn = FakeConnection()
    pool = FakePool(conn)

    monkeypatch.setattr(db_module, "db_pool", pool)
    monkeypatch.setattr(
        db_module,
        "register_vector",
        lambda _conn: (_ for _ in ()).throw(RuntimeError("register failed")),
    )

    # When
    cursor_gen = db_module.get_cursor()
    with pytest.raises(RuntimeError, match="register failed"):
        next(cursor_gen)

    # Then — connection returned with close=True so pool discards it
    assert conn.commit_calls == 0
    assert conn.rollback_calls == 0
    assert pool.putconn_calls == [(conn, True)]
