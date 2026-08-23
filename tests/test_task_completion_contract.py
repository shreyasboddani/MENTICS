import inspect

import app as app_module
from dbhelper import DatabaseHandler
from userhelper import User


def test_lesson_finish_completes_once_without_double_awarding_xp(tmp_path, monkeypatch):
    database = DatabaseHandler(str(tmp_path / "completion.db"))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()

    user_id = database.insert("users", {
        "email": "completion@example.test",
        "password": "not-used",
        "stats": "{}",
        "name": "Completion Test",
        "onboarding_completed": True,
    })
    database.insert("gamification_stats", {
        "user_id": user_id,
        "points": 0,
        "current_streak": 0,
    })
    task_id = database.insert("paths", {
        "user_id": user_id,
        "task_order": 1,
        "description": "Learn the completion contract",
        "is_completed": False,
        "is_active": True,
        "type": "standard",
        "category": "Test Prep",
        "task_format": "lesson",
        "node_type": "lesson",
        "xp_reward": 30,
    })
    lesson_id = database.insert("lessons", {
        "task_id": task_id,
        "title": "Completion contract",
        "skill_key": "completion_contract",
        "skill_label": "Completion contract",
        "subject": "Math",
        "objective": "Finish once",
        "intro": "Intro",
        "recap": "Recap",
        "xp_reward": 30,
    })
    database.insert("lesson_steps", {
        "lesson_id": lesson_id,
        "step_order": 0,
        "step_type": "teach",
        "title": "Learn",
        "body": "One teaching card.",
    })
    user = User(database, "completion@example.test")
    finish_lesson = inspect.unwrap(app_module.lesson_finish)
    finish_task = inspect.unwrap(app_module.api_update_task_status)

    with app_module.app.test_request_context(
        f"/api/lesson/{task_id}/finish", method="POST", json={}
    ):
        first = finish_lesson(user, task_id)
    assert first.get_json()["xp_earned"] == 30

    with app_module.app.test_request_context(
        f"/api/lesson/{task_id}/finish", method="POST", json={}
    ):
        replay = finish_lesson(user, task_id)
    assert replay.get_json()["xp_earned"] == 0

    # A stale client calling the legacy completion endpoint cannot pay the task
    # a second time after the adaptive player has already completed it.
    with app_module.app.test_request_context(
        "/api/update_task_status",
        method="POST",
        json={"taskId": task_id, "status": "complete"},
    ):
        legacy = finish_task(user)
    assert legacy.get_json()["already_completed"] is True

    task = database.select_one("paths", where={"id": task_id})
    game = database.select_one("gamification_stats", where={"user_id": user_id})
    activities = database.select("activity_log", where={
        "user_id": user_id, "activity_type": "task_completed",
    })
    assert task["is_completed"]
    assert task["xp_awarded"] == 30
    assert game["points"] == 30
    assert game["current_streak"] == 1
    assert len(activities) == 1
