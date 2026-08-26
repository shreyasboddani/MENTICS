"""SQLite locally, PostgreSQL when DATABASE_URL is configured."""

import datetime
import re
import sqlite3
from contextlib import contextmanager
from contextvars import ContextVar


_RLS_CONTEXT = ContextVar(
    "mentics_database_rls_context",
    default={"user_id": None, "auth_email": None, "system": False},
)
_UNSET = object()
_REQUEST_CONNECTION = ContextVar("mentics_request_connection", default=None)


class DatabaseTransaction:
    """Small transaction-scoped subset of DatabaseHandler's write API."""

    def __init__(self, database, connection):
        self.database = database
        self.connection = connection

    def insert(self, table_name, data):
        table_name = self.database._identifier(table_name)
        columns = self.database._columns(list(data))
        placeholders = ", ".join(["?"] * len(data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"  # nosec B608
        if self.database.is_postgres and table_name != "gamification_stats":
            query += " RETURNING id"
        cursor = self.connection.cursor()
        cursor.execute(self.database._query(query), tuple(data.values()))
        if self.database.is_postgres:
            row = cursor.fetchone() if query.endswith("RETURNING id") else None
            return row["id"] if row else None
        return cursor.lastrowid

    def update(self, table_name, data, where):
        table_name = self.database._identifier(table_name)
        data_keys = [self.database._identifier(key) for key in data]
        where_keys = [self.database._identifier(key) for key in where]
        set_clause = ", ".join(f"{key}=?" for key in data_keys)
        where_clause = " AND ".join(f"{key}=?" for key in where_keys)
        query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"  # nosec B608
        cursor = self.connection.cursor()
        cursor.execute(
            self.database._query(query),
            tuple(data.values()) + tuple(where.values()),
        )
        return cursor.rowcount

    def execute_write(self, query, params=None):
        """Run a parameterized mutation inside the active transaction."""
        cursor = self.connection.cursor()
        cursor.execute(self.database._query(query), params or ())
        return cursor.rowcount

    def delete(self, table_name, where):
        table_name = self.database._identifier(table_name)
        where_keys = [self.database._identifier(key) for key in where]
        where_clause = " AND ".join(f"{key}=?" for key in where_keys)
        cursor = self.connection.cursor()
        cursor.execute(
            self.database._query(f"DELETE FROM {table_name} WHERE {where_clause}"),  # nosec B608
            tuple(where.values()),
        )
        return cursor.rowcount


class DatabaseHandler:
    _identifier_pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    _order_by_pattern = re.compile(
        r"^[A-Za-z_][A-Za-z0-9_]*(?:\s+(?:ASC|DESC))?(?:\s+LIMIT\s+[1-9][0-9]*)?$",
        flags=re.I,
    )

    def __init__(self, database):
        self.database = database
        self.is_postgres = database.startswith(("postgres://", "postgresql://"))

    def set_rls_context(self, *, user_id=None, auth_email=None, system=False):
        """Bind trusted application identity to subsequent database connections.

        PostgreSQL policies read these transaction/session settings. ContextVar
        keeps concurrent Flask requests and worker threads isolated from each
        other, while SQLite development remains unchanged.
        """
        normalized_user_id = None
        if user_id not in (None, ""):
            normalized_user_id = int(user_id)
            if normalized_user_id <= 0:
                raise ValueError("RLS user id must be positive")
        normalized_email = str(auth_email or "").strip().lower()[:254] or None
        return _RLS_CONTEXT.set({
            "user_id": normalized_user_id,
            "auth_email": normalized_email,
            "system": bool(system),
        })

    def reset_rls_context(self, token):
        _RLS_CONTEXT.reset(token)

    @contextmanager
    def request_scope(self):
        """Reuse one PostgreSQL connection across all queries in a request.

        Vercel can execute several database queries while rendering one page.
        Opening a fresh Neon connection for every query adds avoidable network
        and compute-wakeup latency, especially for users far from the region.
        The connection remains request-local and is always closed at teardown.
        """
        if _REQUEST_CONNECTION.get() is not None:
            yield
            return
        connection = self._connect()
        token = _REQUEST_CONNECTION.set(connection)
        try:
            yield
        finally:
            _REQUEST_CONNECTION.reset(token)
            connection.close()

    @contextmanager
    def rls_scope(self, *, user_id=_UNSET, auth_email=_UNSET, system=_UNSET):
        """Temporarily add auth or tightly scoped system authority."""
        current = _RLS_CONTEXT.get()
        token = self.set_rls_context(
            user_id=current["user_id"] if user_id is _UNSET else user_id,
            auth_email=current["auth_email"] if auth_email is _UNSET else auth_email,
            system=current["system"] if system is _UNSET else system,
        )
        try:
            yield
        finally:
            self.reset_rls_context(token)

    def _connect(self):
        existing = _REQUEST_CONNECTION.get()
        if existing is not None:
            return existing
        if self.is_postgres:
            import psycopg
            from psycopg.rows import dict_row
            connection = psycopg.connect(self.database, row_factory=dict_row)
            context = _RLS_CONTEXT.get()
            # Custom settings are parameterized and set on every fresh
            # connection before any tenant query can run.
            connection.execute(
                "SELECT set_config('mentics.user_id', %s, false), "
                "set_config('mentics.auth_email', %s, false), "
                "set_config('mentics.system', %s, false)",
                (
                    str(context["user_id"] or ""),
                    context["auth_email"] or "",
                    "on" if context["system"] else "off",
                ),
            )
            return connection
        conn = sqlite3.connect(self.database, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def transaction(self):
        """Commit all writes together, rolling every write back on failure."""
        conn = self._connect()
        owns_connection = _REQUEST_CONNECTION.get() is None
        try:
            yield DatabaseTransaction(self, conn)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            if owns_connection:
                conn.close()

    def _query(self, query):
        if not self.is_postgres:
            return query
        query = query.replace("?", "%s")
        query = re.sub(r"\bis_correct\s*=\s*0\b", "is_correct = FALSE", query, flags=re.I)
        return re.sub(r"\bis_correct\s*=\s*1\b", "is_correct = TRUE", query, flags=re.I)

    @classmethod
    def _identifier(cls, value):
        value = str(value)
        if not cls._identifier_pattern.fullmatch(value):
            raise ValueError(f"Unsafe database identifier: {value!r}")
        return value

    @classmethod
    def _columns(cls, columns):
        if columns == "*":
            return "*"
        values = columns if isinstance(columns, (list, tuple)) else [columns]
        return ", ".join(cls._identifier(value) for value in values)

    @classmethod
    def _order_by(cls, value):
        if value and not cls._order_by_pattern.fullmatch(str(value)):
            raise ValueError(f"Unsafe ORDER BY expression: {value!r}")
        return value

    @staticmethod
    def _row(row):
        if row is None:
            return None
        result = dict(row)
        for key, value in result.items():
            if isinstance(value, datetime.datetime):
                result[key] = value.isoformat(sep=" ")
            elif isinstance(value, datetime.date):
                result[key] = value.isoformat()
        return result

    def execute(self, query, params=None):
        conn = self._connect()
        owns_connection = _REQUEST_CONNECTION.get() is None
        try:
            cursor = conn.cursor()
            cursor.execute(self._query(query), params or ())
            verb = query.lstrip().split(None, 1)[0].lower()
            result = [self._row(row) for row in cursor.fetchall()] if verb == "select" else None
            conn.commit()
            return result
        finally:
            if owns_connection:
                conn.close()

    def execute_write(self, query, params=None):
        """Execute a parameterized mutation and return the affected row count."""
        conn = self._connect()
        owns_connection = _REQUEST_CONNECTION.get() is None
        try:
            cursor = conn.cursor()
            cursor.execute(self._query(query), params or ())
            affected = cursor.rowcount
            conn.commit()
            return affected
        finally:
            if owns_connection:
                conn.close()

    def create_table(self, table_name, columns):
        table_name = self._identifier(table_name)
        definitions = []
        for name, column_type in columns.items():
            if self.is_postgres:
                column_type = column_type.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "BIGSERIAL PRIMARY KEY")
            definitions.append(f"{name} {column_type}")
        self.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(definitions)})")

    def add_column(self, table_name, column_name, column_type):
        table_name = self._identifier(table_name)
        column_name = self._identifier(column_name)
        if self.is_postgres:
            self.execute(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} {column_type}")
            return
        try:
            self.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        except sqlite3.OperationalError as error:
            if "duplicate column name" not in str(error).lower():
                raise

    def insert(self, table_name, data):
        table_name = self._identifier(table_name)
        columns = self._columns(list(data))
        placeholders = ", ".join(["?"] * len(data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"  # nosec B608
        conn = self._connect()
        owns_connection = _REQUEST_CONNECTION.get() is None
        try:
            cursor = conn.cursor()
            if self.is_postgres and table_name != "gamification_stats":
                query += " RETURNING id"
            cursor.execute(self._query(query), tuple(data.values()))
            if self.is_postgres:
                row = cursor.fetchone() if query.endswith("RETURNING id") else None
                result = row["id"] if row else None
            else:
                result = cursor.lastrowid
            conn.commit()
            return result
        finally:
            if owns_connection:
                conn.close()

    def update(self, table_name, data, where):
        table_name = self._identifier(table_name)
        data_keys = [self._identifier(key) for key in data]
        where_keys = [self._identifier(key) for key in where]
        set_clause = ", ".join(f"{key}=?" for key in data_keys)
        where_clause = " AND ".join(f"{key}=?" for key in where_keys)
        query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"  # nosec B608
        self.execute(query, tuple(data.values()) + tuple(where.values()))

    def delete(self, table_name, where):
        table_name = self._identifier(table_name)
        where_keys = [self._identifier(key) for key in where]
        where_clause = " AND ".join(f"{key}=?" for key in where_keys)
        query = f"DELETE FROM {table_name} WHERE {where_clause}"  # nosec B608
        self.execute(query, tuple(where.values()))

    def select(self, table_name, columns="*", where=None, order_by=None):
        table_name = self._identifier(table_name)
        columns = self._columns(columns)
        order_by = self._order_by(order_by)
        query = f"SELECT {columns} FROM {table_name}"  # nosec B608
        params = ()
        if where:
            where_keys = [self._identifier(key) for key in where]
            query += " WHERE " + " AND ".join(f"{key}=?" for key in where_keys)
            params = tuple(where.values())
        if order_by:
            query += f" ORDER BY {order_by}"
        return self.execute(query, params)

    def upsert(self, table_name, data, conflict_target):
        table_name = self._identifier(table_name)
        data_keys = [self._identifier(key) for key in data]
        conflict_target = [self._identifier(key) for key in conflict_target]
        columns = ", ".join(data_keys)
        placeholders = ", ".join(["?"] * len(data))
        update_columns = [key for key in data_keys if key not in conflict_target]
        set_clause = ", ".join(f"{key}=excluded.{key}" for key in update_columns)
        query = (f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) "
                 f"ON CONFLICT({', '.join(conflict_target)}) DO UPDATE SET {set_clause}")  # nosec B608
        self.execute(query, tuple(data.values()))

    def execute_returning_one(self, query, params=None):
        """Run a mutation that RETURNS a row and commit it, e.g. an atomic upsert."""
        conn = self._connect()
        owns_connection = _REQUEST_CONNECTION.get() is None
        try:
            cursor = conn.cursor()
            cursor.execute(self._query(query), params or ())
            row = cursor.fetchone()
            result = self._row(row)
            conn.commit()
            return result
        finally:
            if owns_connection:
                conn.close()

    def execute_for_one(self, query, params=None):
        conn = self._connect()
        owns_connection = _REQUEST_CONNECTION.get() is None
        try:
            cursor = conn.cursor()
            cursor.execute(self._query(query), params or ())
            return self._row(cursor.fetchone())
        finally:
            if owns_connection:
                conn.close()

    def select_one(self, table_name, columns="*", where=None, order_by=None):
        table_name = self._identifier(table_name)
        columns = self._columns(columns)
        order_by = self._order_by(order_by)
        query = f"SELECT {columns} FROM {table_name}"  # nosec B608
        params = ()
        if where:
            where_keys = [self._identifier(key) for key in where]
            query += " WHERE " + " AND ".join(f"{key}=?" for key in where_keys)
            params = tuple(where.values())
        if order_by:
            query += f" ORDER BY {order_by}"
        return self.execute_for_one(query + " LIMIT 1", params)
