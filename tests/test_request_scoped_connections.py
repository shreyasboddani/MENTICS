"""Guards for the connection a request pins for the whole of its lifetime.

Reusing one Neon connection per request is a latency win, but it makes every
query share the fate of the one before it: a failed statement leaves PostgreSQL
in an aborted transaction, and session-level RLS settings pushed at connect time
outlive the statement that set them.
"""

import psycopg
import pytest

import ratelimit
from dbhelper import DatabaseHandler


class StatementFailed(Exception):
    """Stands in for a psycopg error such as InsufficientPrivilege."""


class TransactionAborted(Exception):
    """Stands in for psycopg's InFailedSqlTransaction."""


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.rowcount = 0
        self.lastrowid = 1

    def execute(self, sql, params=()):
        self.connection.run(sql)

    def fetchone(self):
        return self.connection.next_row

    def fetchall(self):
        return [self.connection.next_row] if self.connection.next_row else []


class FakeConnection:
    """The parts of a psycopg connection the helper touches.

    Crucially it reproduces PostgreSQL's aborted-transaction state: once a
    statement fails, everything else errors until someone rolls back.
    """

    def __init__(self, fail_on=None, next_row=None):
        self.statements = []
        self.settings = []
        self.rollbacks = 0
        self.aborted = False
        self.fail_on = fail_on
        self.next_row = next_row

    def run(self, sql):
        if self.aborted:
            raise TransactionAborted("current transaction is aborted")
        self.statements.append(sql)
        if self.fail_on and self.fail_on in sql:
            self.aborted = True
            raise StatementFailed("permission denied for schema public")

    def execute(self, sql, params=()):
        self.run(sql)
        if "set_config" in sql:
            self.settings.append(params)
        return self

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        if self.aborted:
            raise TransactionAborted("cannot commit an aborted transaction")

    def rollback(self):
        self.aborted = False
        self.rollbacks += 1

    def close(self):
        pass


def _handler(monkeypatch, connection):
    monkeypatch.setattr(psycopg, "connect", lambda *args, **kwargs: connection)
    return DatabaseHandler("postgresql://mentics/neondb")


def test_a_tolerated_failure_leaves_the_request_connection_usable(monkeypatch):
    # The rate limiter swallows its own errors, so a statement it cannot run
    # must not decide the fate of the sign-in lookup that follows it.
    connection = FakeConnection(fail_on="CREATE TABLE")
    database = _handler(monkeypatch, connection)

    with database.request_scope():
        with pytest.raises(StatementFailed):
            database.execute("CREATE TABLE IF NOT EXISTS rate_limits (bucket TEXT)")

        connection.next_row = {"id": 7, "email": "student@example.com"}
        found = database.select_one("users", where={"email": "student@example.com"})

    assert found["id"] == 7
    assert connection.rollbacks == 1


def test_rls_scope_reaches_an_already_open_request_connection(monkeypatch):
    connection = FakeConnection(next_row={"id": 7})
    database = _handler(monkeypatch, connection)

    with database.request_scope():
        assert connection.settings == [("", "", "off")]

        with database.rls_scope(auth_email="Student@Example.com"):
            database.select_one("users", where={"email": "student@example.com"})
            assert connection.settings[-1] == ("", "student@example.com", "off")

        # Leaving the scope has to surrender the elevated identity again.
        database.select_one("users", where={"email": "student@example.com"})
        assert connection.settings[-1] == ("", "", "off")


def test_an_unchanged_identity_is_not_pushed_again(monkeypatch):
    # Re-pushing on every query would give back the round trip the scoped
    # connection was introduced to save.
    connection = FakeConnection(next_row={"id": 7})
    database = _handler(monkeypatch, connection)

    with database.request_scope():
        for _ in range(3):
            database.select_one("users", where={"email": "student@example.com"})

    assert len(connection.settings) == 1


def test_ensure_table_skips_the_create_it_is_not_allowed_to_run(monkeypatch):
    connection = FakeConnection(fail_on="CREATE TABLE", next_row={"found": "rate_limits"})
    database = _handler(monkeypatch, connection)
    monkeypatch.setattr(ratelimit, "_table_ready", False)

    ratelimit.ensure_table(database)

    assert ratelimit._table_ready
    assert not any("CREATE TABLE" in statement for statement in connection.statements)


def test_ensure_table_still_creates_a_missing_table(monkeypatch):
    connection = FakeConnection(next_row={"found": None})
    database = _handler(monkeypatch, connection)
    monkeypatch.setattr(ratelimit, "_table_ready", False)

    ratelimit.ensure_table(database)

    assert any("CREATE TABLE" in statement for statement in connection.statements)
