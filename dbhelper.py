"""SQLite locally, PostgreSQL when DATABASE_URL is configured."""

import datetime
import re
import sqlite3


class DatabaseHandler:
    def __init__(self, database):
        self.database = database
        self.is_postgres = database.startswith(("postgres://", "postgresql://"))

    def _connect(self):
        if self.is_postgres:
            import psycopg
            from psycopg.rows import dict_row
            return psycopg.connect(self.database, row_factory=dict_row)
        conn = sqlite3.connect(self.database, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _query(self, query):
        if not self.is_postgres:
            return query
        query = query.replace("?", "%s")
        query = re.sub(r"\bis_correct\s*=\s*0\b", "is_correct = FALSE", query, flags=re.I)
        return re.sub(r"\bis_correct\s*=\s*1\b", "is_correct = TRUE", query, flags=re.I)

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
        try:
            cursor = conn.cursor()
            cursor.execute(self._query(query), params or ())
            verb = query.lstrip().split(None, 1)[0].lower()
            result = [self._row(row) for row in cursor.fetchall()] if verb == "select" else None
            conn.commit()
            return result
        finally:
            conn.close()

    def create_table(self, table_name, columns):
        definitions = []
        for name, column_type in columns.items():
            if self.is_postgres:
                column_type = column_type.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "BIGSERIAL PRIMARY KEY")
            definitions.append(f"{name} {column_type}")
        self.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(definitions)})")

    def add_column(self, table_name, column_name, column_type):
        if self.is_postgres:
            self.execute(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} {column_type}")
            return
        try:
            self.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        except sqlite3.OperationalError as error:
            if "duplicate column name" not in str(error).lower():
                raise

    def insert(self, table_name, data):
        columns = ", ".join(data)
        placeholders = ", ".join(["?"] * len(data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        conn = self._connect()
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
            conn.close()

    def update(self, table_name, data, where):
        set_clause = ", ".join(f"{key}=?" for key in data)
        where_clause = " AND ".join(f"{key}=?" for key in where)
        self.execute(f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}", tuple(data.values()) + tuple(where.values()))

    def delete(self, table_name, where):
        where_clause = " AND ".join(f"{key}=?" for key in where)
        self.execute(f"DELETE FROM {table_name} WHERE {where_clause}", tuple(where.values()))

    def select(self, table_name, columns="*", where=None, order_by=None):
        columns = ", ".join(columns) if isinstance(columns, list) else columns
        query = f"SELECT {columns} FROM {table_name}"
        params = ()
        if where:
            query += " WHERE " + " AND ".join(f"{key}=?" for key in where)
            params = tuple(where.values())
        if order_by:
            query += f" ORDER BY {order_by}"
        return self.execute(query, params)

    def upsert(self, table_name, data, conflict_target):
        columns = ", ".join(data)
        placeholders = ", ".join(["?"] * len(data))
        update_columns = [key for key in data if key not in conflict_target]
        set_clause = ", ".join(f"{key}=excluded.{key}" for key in update_columns)
        query = (f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) "
                 f"ON CONFLICT({', '.join(conflict_target)}) DO UPDATE SET {set_clause}")
        self.execute(query, tuple(data.values()))

    def execute_for_one(self, query, params=None):
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(self._query(query), params or ())
            return self._row(cursor.fetchone())
        finally:
            conn.close()

    def select_one(self, table_name, columns="*", where=None, order_by=None):
        columns = ", ".join(columns) if isinstance(columns, list) else columns
        query = f"SELECT {columns} FROM {table_name}"
        params = ()
        if where:
            query += " WHERE " + " AND ".join(f"{key}=?" for key in where)
            params = tuple(where.values())
        if order_by:
            query += f" ORDER BY {order_by}"
        return self.execute_for_one(query + " LIMIT 1", params)
