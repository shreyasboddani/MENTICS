"""Portable schema shared by SQLite development and the Postgres migration."""
TABLES = {
    'learning_hints': {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT', 'user_id': 'INTEGER NOT NULL',
        'source': 'TEXT NOT NULL', 'source_id': 'TEXT NOT NULL',
        'hint_count': 'INTEGER NOT NULL DEFAULT 0', 'UNIQUE': '(user_id, source, source_id)',
    },
    'adaptive_tracks': {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT', 'user_id': 'INTEGER NOT NULL',
        'track_key': 'TEXT NOT NULL', 'version': 'INTEGER NOT NULL DEFAULT 2',
        'benchmark_session_id': 'INTEGER', 'benchmark_completed_at': 'TEXT',
        'diagnostic': "TEXT NOT NULL DEFAULT '{}'", 'generation_token': 'TEXT',
        'generation_started': 'REAL', 'generation_error': 'TEXT',
        'UNIQUE': '(user_id, track_key)',
    },
    'adaptive_sessions': {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT', 'user_id': 'INTEGER NOT NULL',
        'track_key': 'TEXT NOT NULL', 'kind': 'TEXT NOT NULL',
        'status': "TEXT NOT NULL DEFAULT 'generating'", 'request_key': 'TEXT NOT NULL',
        'questions': "TEXT NOT NULL DEFAULT '[]'", 'answers': "TEXT NOT NULL DEFAULT '{}'",
        'hint_usage': "TEXT NOT NULL DEFAULT '{}'", 'profile_snapshot': "TEXT NOT NULL DEFAULT '{}'",
        'summary': "TEXT NOT NULL DEFAULT '{}'", 'generation_note': 'TEXT',
        'created_at': 'REAL NOT NULL', 'updated_at': 'REAL NOT NULL',
        'UNIQUE': '(user_id, request_key)',
    },
    'learning_events': {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT', 'user_id': 'INTEGER NOT NULL',
        'track_key': 'TEXT NOT NULL', 'source': 'TEXT NOT NULL', 'source_id': 'TEXT NOT NULL',
        'skill_key': 'TEXT NOT NULL', 'subskill': 'TEXT NOT NULL', 'domain': 'TEXT NOT NULL',
        'difficulty': 'TEXT NOT NULL', 'is_correct': 'BOOLEAN NOT NULL',
        'response_ms': 'INTEGER', 'hint_count': 'INTEGER NOT NULL DEFAULT 0',
        'confidence': 'INTEGER', 'misconception': 'TEXT', 'evidence': "TEXT NOT NULL DEFAULT '{}'",
        'created_at': 'REAL NOT NULL', 'UNIQUE': '(user_id, source, source_id)',
    },
    'path_generations': {
        'id': 'INTEGER PRIMARY KEY AUTOINCREMENT', 'user_id': 'INTEGER NOT NULL',
        'track_key': 'TEXT NOT NULL', 'request_key': 'TEXT NOT NULL',
        'status': 'TEXT NOT NULL', 'profile_snapshot': 'TEXT NOT NULL',
        'task_ids': "TEXT NOT NULL DEFAULT '[]'", 'note': 'TEXT', 'created_at': 'REAL NOT NULL',
        'UNIQUE': '(user_id, request_key)',
    },
}


def init(db):
    db.add_column('paths', 'learning_version', 'INTEGER NOT NULL DEFAULT 1')
    for table in ('quiz_questions', 'sprint_questions', 'lesson_steps'):
        db.add_column(table, 'adaptive_meta', "TEXT NOT NULL DEFAULT '{}'")
    for table, columns in TABLES.items():
        db.create_table(table, columns)
    db.execute('CREATE INDEX IF NOT EXISTS idx_learning_events_profile ON learning_events(user_id, track_key, created_at)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_adaptive_session_resume ON adaptive_sessions(user_id, track_key, kind, status)')


def postgres_sql():
    statements = ['BEGIN;', 'ALTER TABLE paths ADD COLUMN IF NOT EXISTS learning_version INTEGER NOT NULL DEFAULT 1;']
    for table in ('quiz_questions', 'sprint_questions', 'lesson_steps'):
        statements.append(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS adaptive_meta TEXT NOT NULL DEFAULT '{{}}';")
    for table, columns in TABLES.items():
        definitions = [name + ' ' + spec.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'BIGSERIAL PRIMARY KEY').replace('REAL', 'DOUBLE PRECISION') for name, spec in columns.items()]
        statements.append(f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(definitions)});")
        statements.extend([
            f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;',
            f'ALTER TABLE {table} FORCE ROW LEVEL SECURITY;',
            f'DROP POLICY IF EXISTS mentics_owner ON {table};',
            f'CREATE POLICY mentics_owner ON {table} TO mentics_app USING (user_id=mentics_current_user_id()) WITH CHECK (user_id=mentics_current_user_id());',
            f'GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO mentics_app;',
            f'GRANT USAGE, SELECT ON SEQUENCE {table}_id_seq TO mentics_app;',
        ])
    statements.extend([
        'CREATE INDEX IF NOT EXISTS idx_learning_events_profile ON learning_events(user_id, track_key, created_at);',
        'CREATE INDEX IF NOT EXISTS idx_adaptive_session_resume ON adaptive_sessions(user_id, track_key, kind, status);',
        # Additive rollout: archive only old generated test-prep rows. Their
        # content, results and account XP remain available as historical evidence.
        "UPDATE paths SET is_active=FALSE WHERE category='Test Prep' AND is_user_added=FALSE AND learning_version<2;",
        'COMMIT;',
    ])
    return '\n'.join(statements) + '\n'
