import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "migrations" / "001_enable_rls.sql"

APPLICATION_TABLES = {
    "users",
    "paths",
    "subtasks",
    "stat_history",
    "chat_conversations",
    "activity_log",
    "gamification_stats",
    "forum_posts",
    "forum_replies",
    "sat_battles",
    "sat_battle_stats",
    "quizzes",
    "quiz_questions",
    "quiz_results",
    "practice_sprints",
    "sprint_questions",
    "sprint_results",
    "official_questions",
    "strategy_articles",
    "lessons",
    "lesson_steps",
    "lesson_progress",
    "lesson_answers",
    "skill_mastery",
    "mistake_bank",
    "rate_limits",
}


def test_every_application_table_has_forced_rls():
    sql = MIGRATION.read_text(encoding="utf-8")
    enabled = set(re.findall(r"ALTER TABLE (\w+) ENABLE ROW LEVEL SECURITY", sql))
    forced = set(re.findall(r"ALTER TABLE (\w+) FORCE ROW LEVEL SECURITY", sql))

    assert enabled == APPLICATION_TABLES
    assert forced == APPLICATION_TABLES


def test_runtime_role_cannot_bypass_rls_and_gets_no_schema_create():
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "mentics_app must not have BYPASSRLS" in sql
    assert "REVOKE CREATE ON SCHEMA public FROM mentics_app" in sql
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES" in sql


def test_all_policies_are_scoped_to_runtime_role():
    sql = MIGRATION.read_text(encoding="utf-8")
    policies = re.findall(
        r"CREATE POLICY\s+\w+\s+ON\s+\w+(?:\s+FOR\s+\w+)?\s+TO\s+(\w+)",
        sql,
        flags=re.IGNORECASE,
    )

    assert policies
    assert set(policies) == {"mentics_app"}
