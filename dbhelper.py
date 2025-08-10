import sqlite3


class DatabaseHandler:
    def __init__(self, db_name):
        self.db_name = db_name

    def execute(self, query, params=None):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        if params:
            c.execute(query, params)
        else:
            c.execute(query)
        verb = query.strip().lower().split()[0]
        if verb == "select":
            result = c.fetchall()
        elif verb == "insert":
            result = c.lastrowid
        else:
            result = None
        conn.commit()
        conn.close()
        return result

    def create_table(self, table_name, columns):
        """
        columns: dict of column_name: column_type_and_constraints
        Example: {"id": "INTEGER PRIMARY KEY AUTOINCREMENT", "email": "TEXT NOT NULL UNIQUE"}
        """
        cols = ', '.join([f"{col} {ctype}" for col, ctype in columns.items()])
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({cols})"
        self.execute(query)

    def add_column(self, table_name, column_name, column_type):
        query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        self.execute(query)

    def insert(self, table_name, data):
        """
        data: dict of column_name: value
        """
        cols = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"
        return self.execute(query, tuple(data.values()))

    def update(self, table_name, data, where):
        """
        data: dict of column_name: value
        where: dict of column_name: value for WHERE clause
        """
        set_clause = ', '.join([f"{k}=?" for k in data.keys()])
        where_clause = ' AND '.join([f"{k}=?" for k in where.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        params = tuple(data.values()) + tuple(where.values())
        self.execute(query, params)

    def delete(self, table_name, where):
        """
        where: dict of column_name: value for WHERE clause
        """
        where_clause = ' AND '.join([f"{k}=?" for k in where.keys()])
        query = f"DELETE FROM {table_name} WHERE {where_clause}"
        self.execute(query, tuple(where.values()))

    def select(self, table_name, columns='*', where=None):
        """
        columns: list or str
        where: dict of column_name: value for WHERE clause
        """
        if isinstance(columns, list):
            cols = ', '.join(columns)
        else:
            cols = columns
        query = f"SELECT {cols} FROM {table_name}"
        params = ()
        if where:
            where_clause = ' AND '.join([f"{k}=?" for k in where.keys()])
            query += f" WHERE {where_clause}"
            params = tuple(where.values())
        return self.execute(query, params)
