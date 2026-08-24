import inspect

import app as app_module
from dbhelper import DatabaseHandler
from userhelper import User


def _user(database):
    database.insert("users", {
        "email": "scores@example.test",
        "password": "not-used",
        "stats": "{}",
        "name": "Scores Student",
        "onboarding_completed": True,
    })
    return User(database, "scores@example.test")


def test_academic_snapshot_uses_the_same_profile_and_test_path_values():
    snapshot = app_module._academic_score_snapshot({
        "gpa": 3.82,
        "test_path": {
            "current_sat_ebrw": "710", "current_sat_math": "760",
            "current_act_composite": "33",
        },
    })

    assert snapshot == {
        "gpa": 3.82,
        "satEbrw": 710, "satMath": 760, "satTotal": 1470,
        "actMath": None, "actReading": None, "actScience": None,
        "actComposite": 33, "actAverage": 33,
    }


def test_direct_total_and_composite_updates_persist_to_the_shared_snapshot(tmp_path, monkeypatch):
    database = DatabaseHandler(str(tmp_path / "scores.db"))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()
    user = _user(database)
    update_stats = inspect.unwrap(app_module.api_update_stats)

    with app_module.app.test_request_context(
        "/api/update_stats", method="POST", json={"stat_name": "sat_total", "stat_value": 1480}
    ):
        assert update_stats(user).get_json()["success"] is True
    with app_module.app.test_request_context(
        "/api/update_stats", method="POST", json={"stat_name": "act_composite", "stat_value": 34}
    ):
        assert update_stats(user).get_json()["success"] is True

    refreshed = User(database, "scores@example.test").get_stats()
    snapshot = app_module._academic_score_snapshot(refreshed)
    assert snapshot["satTotal"] == 1480
    assert snapshot["actAverage"] == 34
