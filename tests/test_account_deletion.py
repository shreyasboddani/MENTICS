import inspect
import json

import app as app_module
from dbhelper import DatabaseHandler
from userhelper import User


def _user(database, email, name):
    user_id = database.insert("users", {
        "email": email,
        "password": "not-used",
        "stats": "{}",
        "name": name,
        "onboarding_completed": True,
    })
    return user_id, User(database, email)


def test_account_deletion_erases_account_owned_records(tmp_path, monkeypatch):
    database = DatabaseHandler(str(tmp_path / "account-deletion.db"))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()
    user_id, user = _user(database, "erase@example.test", "Erase Me")
    other_id, _ = _user(database, "keep@example.test", "Keep Me")

    task_id = database.insert("paths", {
        "user_id": user_id, "task_order": 1, "description": "Private task",
        "category": "Test Prep",
    })
    database.insert("subtasks", {"parent_task_id": task_id, "description": "Private subtask"})
    database.insert("stat_history", {"user_id": user_id, "stat_name": "sat_total", "stat_value": "1400"})
    database.insert("chat_conversations", {"user_id": user_id, "category": "Test Prep", "history": "private chat"})
    database.insert("activity_log", {"user_id": user_id, "activity_type": "task_completed", "details": "private"})
    database.insert("gamification_stats", {"user_id": user_id, "points": 40, "current_streak": 2})
    database.insert("skill_mastery", {"user_id": user_id, "skill_key": "algebra", "attempts": 2, "correct": 1})
    database.insert("mistake_bank", {"user_id": user_id, "question_text": "private question"})
    post_id = database.insert("forum_posts", {"user_id": user_id, "user_name": "Erase Me", "title": "Private post", "content": "remove me"})
    database.insert("forum_replies", {"post_id": post_id, "user_id": other_id, "user_name": "Keep Me", "content": "thread reply"})
    database.insert("sat_battles", {
        "status": "complete", "challenger_id": user_id, "challenger_name": "Erase Me",
        "opponent_id": other_id, "opponent_name": "Keep Me", "questions": json.dumps([]),
    })

    account = inspect.unwrap(app_module.account)
    with app_module.app.test_request_context("/account", method="POST", data={
        "form_type": "delete_account", "delete_email": "erase@example.test", "delete_confirmation": "DELETE",
    }):
        response = account(user)

    assert response.status_code == 302
    assert database.select_one("users", where={"id": user_id}) is None
    assert database.select_one("users", where={"id": other_id}) is not None
    assert database.select("paths", where={"user_id": user_id}) == []
    assert database.select("stat_history", where={"user_id": user_id}) == []
    assert database.select("chat_conversations", where={"user_id": user_id}) == []
    assert database.select("activity_log", where={"user_id": user_id}) == []
    assert database.select("gamification_stats", where={"user_id": user_id}) == []
    assert database.select("skill_mastery", where={"user_id": user_id}) == []
    assert database.select("mistake_bank", where={"user_id": user_id}) == []
    assert database.select("forum_posts", where={"user_id": user_id}) == []
    assert database.select("forum_replies", where={"post_id": post_id}) == []
    assert database.execute("SELECT * FROM sat_battles WHERE challenger_id=? OR opponent_id=?", (user_id, user_id)) == []


def test_account_deletion_requires_email_and_typed_confirmation(tmp_path, monkeypatch):
    database = DatabaseHandler(str(tmp_path / "account-confirmation.db"))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()
    user_id, user = _user(database, "confirm@example.test", "Confirm Me")
    account = inspect.unwrap(app_module.account)

    with app_module.app.test_request_context("/account", method="POST", data={
        "form_type": "delete_account", "delete_email": "confirm@example.test", "delete_confirmation": "delete",
    }):
        response = account(user)

    assert response[1] == 400
    assert database.select_one("users", where={"id": user_id}) is not None
