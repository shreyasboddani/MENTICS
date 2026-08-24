import inspect
from datetime import timedelta

import app as app_module
from dbhelper import DatabaseHandler
from userhelper import User


def _user(database, email, name):
    database.insert("users", {
        "email": email,
        "password": "not-used",
        "stats": "{}",
        "name": name,
        "onboarding_completed": True,
    })
    return User(database, email)


def test_sat_battle_matches_two_students_and_only_finishes_once(tmp_path, monkeypatch):
    database = DatabaseHandler(str(tmp_path / "battles.db"))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()
    challenger = _user(database, "challenger@example.test", "Challenger")
    opponent = _user(database, "opponent@example.test", "Opponent")
    queue = inspect.unwrap(app_module.queue_sat_battle)
    submit = inspect.unwrap(app_module.submit_sat_battle)

    with app_module.app.test_request_context("/api/sat-battles/queue", method="POST", json={}):
        waiting = queue(challenger).get_json()
    assert waiting["status"] == "waiting"
    assert "questions" not in waiting

    with app_module.app.test_request_context("/api/sat-battles/queue", method="POST", json={}):
        active = queue(opponent).get_json()
    assert active["status"] == "active"
    assert len(active["questions"]) == app_module.SAT_BATTLE_QUESTION_COUNT
    assert "correct_option" not in active["questions"][0]
    assert active["isBotBattle"] is False

    # The waiting player polls the same battle after a second student joins.
    # Both players must see one live round and an identical shuffled question set.
    challenger_live = app_module._battle_payload(
        database.select_one("sat_battles", where={"id": active["id"]}), challenger.data["id"]
    )
    assert challenger_live["status"] == "active"
    assert challenger_live["opponentName"] == "Opponent"
    assert challenger_live["questions"] == active["questions"]

    answers = [{"question_index": index, "selected_option": 0} for index in range(5)]
    with app_module.app.test_request_context(
        f"/api/sat-battles/{active['id']}/submit", method="POST", json={"answers": answers}
    ):
        first = submit(challenger, active["id"]).get_json()
    assert first["status"] == "active"
    assert first["submitted"] is True

    with app_module.app.test_request_context(
        f"/api/sat-battles/{active['id']}/submit", method="POST", json={"answers": answers}
    ):
        result = submit(opponent, active["id"]).get_json()
    assert result["status"] == "complete"
    assert len(result["answerKey"]) == 5

    battle = database.select_one("sat_battles", where={"id": active["id"]})
    challenger_stats = database.select_one("sat_battle_stats", where={"user_id": challenger.data["id"]})
    opponent_stats = database.select_one("sat_battle_stats", where={"user_id": opponent.data["id"]})
    assert battle["status"] == "complete"
    assert challenger_stats["battles_played"] == 1
    assert opponent_stats["battles_played"] == 1


def test_sat_battle_queues_a_beatable_bot_after_thirty_seconds(tmp_path, monkeypatch):
    database = DatabaseHandler(str(tmp_path / "bot-battle.db"))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()
    challenger = _user(database, "bot-challenger@example.test", "Bot Challenger")
    queue = inspect.unwrap(app_module.queue_sat_battle)

    with app_module.app.test_request_context("/api/sat-battles/queue", method="POST", json={}):
        waiting = queue(challenger).get_json()
    database.update("sat_battles", {
        "created_at": (app_module._utc_now() - timedelta(seconds=31)).isoformat(),
    }, where={"id": waiting["id"]})
    database.delete("users", where={"email": app_module.SAT_BATTLE_BOT_EMAIL})

    active = app_module._battle_payload(
        database.select_one("sat_battles", where={"id": waiting["id"]}), challenger.data["id"]
    )
    assert active["status"] == "active"
    assert active["isBotBattle"] is True
    assert active["opponentName"] == "Mentics Arena Bot"


def test_training_round_starts_immediately_and_does_not_rank(tmp_path, monkeypatch):
    database = DatabaseHandler(str(tmp_path / "training.db"))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()
    challenger = _user(database, "training@example.test", "Training Student")
    train = inspect.unwrap(app_module.train_with_sat_battle_bot)

    with app_module.app.test_request_context("/api/sat-battles/train", method="POST", json={}):
        training = train(challenger).get_json()
    assert training["status"] == "active"
    assert training["mode"] == "training"
    assert training["isBotBattle"] is True


def test_training_room_can_target_every_arena_rank(tmp_path, monkeypatch):
    database = DatabaseHandler(str(tmp_path / "tiered-training.db"))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()
    challenger = _user(database, "tiered-training@example.test", "Tiered Student")
    train = inspect.unwrap(app_module.train_with_sat_battle_bot)

    for rank, label in [
        ("bronze", "Bronze"), ("silver", "Silver"), ("gold", "Gold"),
        ("platinum", "Platinum"), ("diamond", "Diamond"), ("master", "Master"),
        ("grandmaster", "Grandmaster"),
    ]:
        with app_module.app.test_request_context("/api/sat-battles/train", method="POST", json={"rank": rank}):
            training = train(challenger).get_json()
        assert training["mode"] == "training"
        assert training["difficulty"] == rank
        assert training["opponentName"] == f"Mentics {label} Bot"
        database.update("sat_battles", {"status": "expired"}, where={"id": training["id"]})


def test_training_round_supports_the_original_arena_table_without_mode(tmp_path, monkeypatch):
    database = DatabaseHandler(str(tmp_path / "legacy-training.db"))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()
    # The first production Arena release created this table before `mode` was
    # introduced. Keep training usable while a deployment is awaiting migration.
    database.execute("ALTER TABLE sat_battles RENAME TO sat_battles_with_mode")
    database.execute("""
        CREATE TABLE sat_battles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL,
            challenger_id INTEGER NOT NULL,
            challenger_name TEXT NOT NULL,
            opponent_id INTEGER,
            opponent_name TEXT,
            questions TEXT NOT NULL,
            challenger_answers TEXT,
            opponent_answers TEXT,
            challenger_finished_at TEXT,
            opponent_finished_at TEXT,
            started_at TEXT,
            winner_id INTEGER,
            completed_at TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    challenger = _user(database, "legacy-training@example.test", "Legacy Student")
    train = inspect.unwrap(app_module.train_with_sat_battle_bot)

    with app_module.app.test_request_context("/api/sat-battles/train", method="POST", json={}):
        training = train(challenger).get_json()

    stored = database.select_one("sat_battles", where={"id": training["id"]})
    assert training["mode"] == "training"
    assert stored["opponent_name"] == "Mentics Training Bot"


def test_sat_battle_rank_ladder_covers_bronze_through_grandmaster():
    assert app_module._battle_rank(1000)["label"] == "Bronze"
    assert app_module._battle_rank(1050)["label"] == "Silver"
    assert app_module._battle_rank(1150)["label"] == "Gold"
    assert app_module._battle_rank(1250)["label"] == "Platinum"
    assert app_module._battle_rank(1400)["label"] == "Diamond"
    assert app_module._battle_rank(1550)["label"] == "Master"
    assert app_module._battle_rank(1750)["label"] == "Grandmaster"


def test_sat_battle_questions_are_original_sat_style_and_scale_by_rank():
    tiers = {
        "bronze": 1000, "silver": 1050, "gold": 1150, "platinum": 1250,
        "diamond": 1400, "master": 1550, "grandmaster": 1750,
    }
    prompts = {}
    for tier, rating in tiers.items():
        bank = app_module.SAT_BATTLE_QUESTION_BANK[tier]
        assert len(bank) >= app_module.SAT_BATTLE_QUESTION_COUNT
        assert min(len(question["question_text"]) for question in bank) >= 75
        assert sum(len(question["question_text"]) for question in bank) / len(bank) >= 140
        assert len({question["skill"] for question in bank}) >= 4
        questions = app_module._battle_questions(rating)
        assert len(questions) == app_module.SAT_BATTLE_QUESTION_COUNT
        assert {question["difficulty"] for question in questions} == {tier}
        assert all(question["question_text"] and question["skill"] for question in questions)
        assert all(len(question["options"]) == 4 for question in questions)
        assert all(0 <= question["correct_option"] < 4 for question in questions)
        prompts[tier] = {question["question_text"] for question in questions}
    assert prompts["bronze"].isdisjoint(prompts["grandmaster"])


def test_training_bots_scale_their_accuracy_with_the_selected_rank():
    expected_scores = {
        "bronze": 2, "silver": 2, "gold": 3, "platinum": 3,
        "diamond": 4, "master": 4, "grandmaster": 5,
    }
    for tier, expected_score in expected_scores.items():
        rating = next(minimum for minimum, _label, key in app_module.SAT_BATTLE_RANKS if key == tier)
        questions = app_module._battle_questions(rating)
        assert app_module._battle_score(questions, app_module._battle_bot_answers(questions)) == expected_score


def test_live_match_uses_the_higher_players_question_tier(tmp_path, monkeypatch):
    database = DatabaseHandler(str(tmp_path / "ranked-match.db"))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()
    bronze = _user(database, "bronze@example.test", "Bronze Player")
    grandmaster = _user(database, "grandmaster@example.test", "Grandmaster Player")
    database.insert("sat_battle_stats", {
        "user_id": grandmaster.data["id"], "user_name": "Grandmaster Player", "rating": 1750,
        "wins": 0, "losses": 0, "draws": 0, "battles_played": 0,
    })
    queue = inspect.unwrap(app_module.queue_sat_battle)

    with app_module.app.test_request_context("/api/sat-battles/queue", method="POST", json={}):
        queue(bronze)
    with app_module.app.test_request_context("/api/sat-battles/queue", method="POST", json={}):
        active = queue(grandmaster).get_json()

    assert active["status"] == "active"
    assert active["difficulty"] == "grandmaster"
