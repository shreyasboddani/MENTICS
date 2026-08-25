import inspect
import json
import re
from datetime import timedelta
from pathlib import Path

import pytest

import app as app_module
from dbhelper import DatabaseHandler
from userhelper import User


@pytest.fixture(autouse=True)
def _disable_live_arena_ai(monkeypatch):
    """Arena unit tests must never spend a real Gemini request from .env."""
    monkeypatch.setattr(app_module, "gemini_api_key", None)


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


def test_arena_avatar_loadout_is_validated_and_persisted(tmp_path, monkeypatch):
    database = DatabaseHandler(str(tmp_path / "arena-avatar.db"))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()
    player = _user(database, "fighter@example.test", "Fighter")
    save_avatar = inspect.unwrap(app_module.update_sat_battle_avatar)

    loadout = {
        "frame": "athletic", "body": "titan", "height": "tall", "skin": "deep",
        "eyes": "violet", "brows": "sharp", "expression": "fierce", "face": "scar",
        "facial_hair": "goatee", "hair": "locs", "hair_color": "crimson",
        "outfit": "flight", "palette": "ember", "accent": "lime", "bottom": "pleated",
        "gloves": "claws", "footwear": "greaves", "gear": "helmet",
        "back": "wings", "emblem": "atom", "aura": "storm",
        "pose": "guard", "marking": "circuit", "shoulder": "pauldrons", "waist": "holsters",
    }
    with app_module.app.test_request_context("/api/sat-battles/avatar", method="POST", json=loadout):
        saved = save_avatar(player).get_json()["avatar"]

    assert saved == loadout
    stored = json.loads(database.select_one("users", where={"id": player.data["id"]})["stats"])
    assert stored["arena_avatar"] == saved

    sanitized = app_module._normalize_arena_avatar({"body": "javascript", "palette": "", "gear": 42})
    assert sanitized == app_module.ARENA_AVATAR_DEFAULT

    upgraded = app_module._normalize_arena_avatar({"body": "scout", "hair": "wave"})
    assert upgraded["body"] == "scout"
    assert upgraded["hair"] == "wave"
    assert upgraded["frame"] == "masculine"
    assert upgraded["outfit"] == "combat"

    # A loadout saved before a slot existed must still normalize, filling only
    # the missing slot rather than resetting the fighter the student built.
    legacy = app_module._normalize_arena_avatar({
        "frame": "feminine", "body": "sentinel", "skin": "deep", "hair": "braids",
        "hair_color": "copper", "face": "freckles", "outfit": "champion",
        "palette": "glacier", "accent": "gold", "bottom": "battle_skirt",
        "gloves": "gauntlets", "footwear": "armored", "gear": "crown",
        "back": "cape", "emblem": "mind", "aura": "orbit",
    })
    assert legacy["outfit"] == "champion"
    assert legacy["hair"] == "braids"
    assert legacy["height"] == "average"
    assert legacy["expression"] == "calm"
    assert set(legacy) == set(app_module.ARENA_AVATAR_DEFAULT)


def test_battle_payload_carries_both_fighter_loadouts(tmp_path, monkeypatch):
    database = DatabaseHandler(str(tmp_path / "arena-versus-avatars.db"))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()
    challenger = _user(database, "fighter-one@example.test", "Fighter One")
    opponent = _user(database, "fighter-two@example.test", "Fighter Two")
    challenger.set_stats({"arena_avatar": {"body": "scout", "palette": "solar", "gear": "comms", "aura": "flare"}})
    opponent.set_stats({"arena_avatar": {"body": "sentinel", "palette": "volt", "gear": "crown", "aura": "orbit"}})
    queue = inspect.unwrap(app_module.queue_sat_battle)

    with app_module.app.test_request_context("/api/sat-battles/queue", method="POST", json={}):
        queue(challenger)
    with app_module.app.test_request_context("/api/sat-battles/queue", method="POST", json={}):
        active = queue(opponent).get_json()

    assert active["playerAvatar"]["palette"] == "volt"
    assert active["opponentAvatar"]["palette"] == "solar"


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


def test_sat_battle_round_uses_a_fresh_validated_ai_set_when_configured(tmp_path, monkeypatch):
    database = DatabaseHandler(str(tmp_path / "ai-arena.db"))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()
    generated = {"questions": []}
    for index in range(3):
        generated["questions"].append({
            "domain": "math",
            "question_text": (
                f"For a positive constant parameter k{index}, a nonlinear system has two roots that satisfy "
                "a stated ratio and an additional area constraint. The greater root is three times the lesser "
                "root, while the related similar figure has twice its area. Which value satisfies every condition?"
            ),
            "options": [f"Choice {index}A", f"Choice {index}B", f"Choice {index}C", f"Choice {index}D"],
            "correct_option": index % 4,
            "skill": f"Advanced math skill {index}",
            "explanation": "The correct choice follows from every supplied constraint; a tempting wrong choice skips the root-ratio condition.",
        })
    for index in range(3, 5):
        generated["questions"].append({
            "domain": "reading_writing",
            "question_text": (
                f"Text {index}: Researchers compared two explanations for an unexpected result. "
                + " ".join(["idea"] * 105)
                + " Which choice is most precisely supported by the relationship between the claims?"
            ),
            "options": [f"Choice {index}A", f"Choice {index}B", f"Choice {index}C", f"Choice {index}D"],
            "correct_option": index % 4,
            "skill": f"Advanced reading skill {index}",
            "explanation": "The correct choice matches the scope of both claims; a tempting wrong choice reverses the direction of support.",
        })
    calls = []

    def generate(prompt, **kwargs):
        calls.append((prompt, kwargs))
        slot_match = re.search(r"Slot: (\d) of 5", prompt)
        skill_match = re.search(r'Advanced (?:math|reading) skill (\d)', prompt)
        slot = int(slot_match.group(1)) - 1 if slot_match else int(skill_match.group(1))
        return json.dumps({"question": generated["questions"][slot]})

    monkeypatch.setattr(app_module, "gemini_api_key", "test-key")
    monkeypatch.setattr(app_module, "_get_gemini_client", lambda: object())
    monkeypatch.setattr(app_module, "_generate_text", generate)
    questions = app_module._battle_questions(1750)

    assert len(calls) == 10
    assert all("GRANDMASTER" in call[0] for call in calls)
    creation_calls = [call for call in calls if "Slot:" in call[0]]
    review_calls = [call for call in calls if "Independently audit" in call[0]]
    assert {int(re.search(r"Slot: (\d) of 5", call[0]).group(1)) for call in creation_calls} == {1, 2, 3, 4, 5}
    assert all(call[1]["model"] == app_module.GEMINI_ARENA_MODEL for call in calls)
    assert all(call[1]["thinking_level"] == "medium" for call in creation_calls)
    assert all(call[1]["thinking_level"] == "medium" for call in review_calls)
    assert {question["difficulty"] for question in questions} == {"grandmaster"}
    assert {question["source"] for question in questions} == {"gemini"}
    assert all(question["explanation"] for question in questions)
    assert {question["skill"] for question in questions} == {
        "Advanced math skill 0", "Advanced math skill 1", "Advanced math skill 2",
        "Advanced reading skill 3", "Advanced reading skill 4",
    }


def test_waiting_arena_match_defers_ai_generation_until_it_becomes_a_round(tmp_path, monkeypatch):
    database = DatabaseHandler(str(tmp_path / "deferred-ai-arena.db"))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()
    challenger = _user(database, "deferred-ai@example.test", "Deferred AI")
    queue = inspect.unwrap(app_module.queue_sat_battle)
    monkeypatch.setattr(app_module, "gemini_api_key", "test-key")
    monkeypatch.setattr(app_module, "_generate_text", lambda *_args, **_kwargs: pytest.fail("AI should not run while a match is merely waiting"))

    with app_module.app.test_request_context("/api/sat-battles/queue", method="POST", json={}):
        waiting = queue(challenger).get_json()

    stored = database.select_one("sat_battles", where={"id": waiting["id"]})
    assert waiting["status"] == "waiting"
    assert json.loads(stored["questions"]) == []


def test_configured_training_never_silently_reuses_the_fallback_bank(tmp_path, monkeypatch):
    database = DatabaseHandler(str(tmp_path / "strict-ai-training.db"))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()
    challenger = _user(database, "strict-ai@example.test", "Strict AI")
    train = inspect.unwrap(app_module.train_with_sat_battle_bot)
    monkeypatch.setattr(app_module, "gemini_api_key", "test-key")
    monkeypatch.setattr(app_module, "_generate_ai_battle_questions", lambda _difficulty: None)

    with app_module.app.test_request_context("/api/sat-battles/train", method="POST", json={"rank": "grandmaster"}):
        response, status = train(challenger)

    assert status == 503
    assert "Gemini" in response.get_json()["error"]
    assert database.execute("SELECT * FROM sat_battles") == []


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


# --- Grandmaster round assembly --------------------------------------------
# Grandmaster is the tier where a single weak slot used to cost the student the
# whole round: one attempt, whole-set validation, and any slot raising ended the
# request in a 503. These cover the per-slot retry that replaced it.

_GRANDMASTER_MATH = {
    0: (
        "For a positive constant k, the function f(x) = x² - 2kx + k² - 9 has two distinct real "
        "zeros, and the vertex of its graph lies on the line y = -9. A second constant m satisfies "
        "f(m) = 0 and m > k. Which value of k makes the greater zero exactly four times the lesser "
        "zero, given that both zeros are positive and every stated condition holds simultaneously?"
    ),
    1: (
        "A survey sampled 480 students and recorded whether each takes a bus and whether each joins a "
        "club. The two-way table is partly lost: 260 students take a bus, and the conditional "
        "probability that a student joins a club given that the student takes a bus is 0.35. Among "
        "students who do not take a bus, the ratio of club members to non-members is 3 to 5. What is "
        "the probability that a randomly chosen club member does not take a bus?"
    ),
    2: (
        "In the coordinate plane, circle C has an unknown radius r and center (h, 4), where h is a "
        "constant. Circle C passes through (0, 0), and a chord of C joining (0, 0) to (8, 0) has a "
        "midpoint whose distance to the center is 3. A similar circle scaled by a factor of 2 about "
        "the origin has area 100π. What is the value of h, given that every condition above holds?"
    ),
}
# The geometry slot draft below is well formed but never names a constrained
# measurement, so it should be retried rather than accepted or thrown away.
_GRANDMASTER_LOOSE_MATH = (
    "A shipping crate is packed with identical cubes. The crate holds twice as many cubes along its "
    "longest edge as along its shortest edge, and the packer reports that reversing two of the edge "
    "counts would change nothing about how the cubes fit inside. How many cubes fill the crate if "
    "the middle edge count is exactly seven and no cube is cut or left over anywhere in the crate?"
)


def _grandmaster_reading(index):
    body = " ".join(["evidence"] * 118)
    return (
        f"Text {index}: Two researchers reached different conclusions from the same field record. "
        f"{body} Which choice best describes the relationship between the two accounts?"
    )


def _grandmaster_item(slot, *, math_text=None):
    if slot < 3:
        return {
            "domain": "math",
            "question_text": math_text or _GRANDMASTER_MATH[slot],
            "options": [f"Slot {slot} choice {letter}" for letter in "ABCD"],
            "correct_option": slot % 4,
            "skill": f"Advanced math skill {slot}",
            "explanation": "Substituting the key back satisfies every constraint; the tempting wrong choice drops one condition.",
        }
    return {
        "domain": "reading_writing",
        "question_text": _grandmaster_reading(slot),
        "options": [f"Slot {slot} choice {letter}" for letter in "ABCD"],
        "correct_option": slot % 4,
        "skill": f"Advanced reading skill {slot}",
        "explanation": "The key matches the scope of both accounts; the tempting wrong choice reverses the direction of support.",
    }


def _arena_generator(script):
    """Return a fake _generate_text driven by {slot: [item, item, ...]}.

    Creation calls pop the next scripted item for their slot, and audit calls
    echo whatever draft they were handed, so a test only has to describe what
    the writer produces on each attempt.
    """
    calls = []

    def generate(prompt, **kwargs):
        calls.append(prompt)
        if "Independently audit" in prompt:
            draft = json.loads(prompt.split("DRAFT:\n", 1)[1])
            return json.dumps(draft)
        slot = int(re.search(r"Slot: (\d) of 5", prompt).group(1)) - 1
        item = script[slot].pop(0)
        if isinstance(item, Exception):
            raise item
        return json.dumps({"question": item})

    return generate, calls


def _arena_database(tmp_path, monkeypatch, name):
    database = DatabaseHandler(str(tmp_path / name))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()
    monkeypatch.setattr(app_module, "gemini_api_key", "test-key")
    monkeypatch.setattr(app_module, "_get_gemini_client", lambda: object())
    return database


def test_grandmaster_round_regenerates_only_the_slot_that_missed_its_contract(tmp_path, monkeypatch):
    _arena_database(tmp_path, monkeypatch, "gm-retry.db")
    script = {slot: [_grandmaster_item(slot)] for slot in range(5)}
    script[2] = [_grandmaster_item(2, math_text=_GRANDMASTER_LOOSE_MATH), _grandmaster_item(2)]
    generate, calls = _arena_generator(script)
    monkeypatch.setattr(app_module, "_generate_text", generate)

    questions = app_module._battle_questions(1750)

    assert len(questions) == app_module.SAT_BATTLE_QUESTION_COUNT
    assert {question["source"] for question in questions} == {"gemini"}
    # The off-brief draft was replaced, not shipped.
    assert questions[2]["question_text"] == _GRANDMASTER_MATH[2]
    # Only the geometry slot was written twice; the other four were left alone.
    slots_written = [int(re.search(r"Slot: (\d) of 5", call).group(1)) for call in calls if "Slot:" in call]
    assert sorted(slots_written) == [1, 2, 3, 3, 4, 5]


def test_grandmaster_round_survives_a_slot_whose_generation_raises(tmp_path, monkeypatch):
    _arena_database(tmp_path, monkeypatch, "gm-raise.db")
    script = {slot: [_grandmaster_item(slot)] for slot in range(5)}
    script[4] = [ValueError("Gemini returned an empty response."), _grandmaster_item(4)]
    generate, _calls = _arena_generator(script)
    monkeypatch.setattr(app_module, "_generate_text", generate)

    questions = app_module._battle_questions(1750)

    assert len(questions) == app_module.SAT_BATTLE_QUESTION_COUNT
    assert questions[4]["domain"] == "reading_writing"
    assert {question["difficulty"] for question in questions} == {"grandmaster"}


def test_grandmaster_settles_for_a_valid_item_rather_than_failing_the_round(tmp_path, monkeypatch):
    """A stylistic miss must not cost a student their round.

    The item contract -- solvable, four distinct choices, one key, in scope, not
    a repeat -- is never relaxed. The tier's slot brief is retried three times
    and then conceded, because an off-brief Grandmaster item still beats a 503.
    """
    _arena_database(tmp_path, monkeypatch, "gm-settle.db")
    script = {slot: [_grandmaster_item(slot) for _ in range(4)] for slot in range(5)}
    script[2] = [_grandmaster_item(2, math_text=_GRANDMASTER_LOOSE_MATH) for _ in range(4)]
    generate, calls = _arena_generator(script)
    monkeypatch.setattr(app_module, "_generate_text", generate)

    questions = app_module._battle_questions(1750)

    assert len(questions) == app_module.SAT_BATTLE_QUESTION_COUNT
    assert questions[2]["question_text"] == _GRANDMASTER_LOOSE_MATH
    # It only settled after genuinely retrying that slot.
    assert sum("Slot: 3 of 5" in call for call in calls) == app_module.SAT_BATTLE_SLOT_ATTEMPTS


def test_grandmaster_still_refuses_a_malformed_item(tmp_path, monkeypatch):
    """The non-negotiable half of the contract stays non-negotiable."""
    _arena_database(tmp_path, monkeypatch, "gm-malformed.db")
    broken = _grandmaster_item(1)
    broken["options"] = ["Same", "Same", "Same", "Same"]
    script = {slot: [_grandmaster_item(slot) for _ in range(4)] for slot in range(5)}
    script[1] = [broken for _ in range(4)]
    generate, _calls = _arena_generator(script)
    monkeypatch.setattr(app_module, "_generate_text", generate)

    assert app_module._generate_ai_battle_questions("grandmaster") is None


def test_arena_avatar_slots_match_the_renderer_catalog():
    """The allow-list and the drawing must describe the same fighter.

    A value the server accepts but the renderer cannot draw shows the student a
    default; a value the locker offers but the server rejects silently discards
    their choice on save. Both are invisible in manual testing, so they are
    pinned here instead.
    """
    source = (Path(__file__).resolve().parents[1] / "frontend" / "src" / "arena-fighter.jsx").read_text(encoding="utf-8")
    catalog = source.split("ARENA_CUSTOMIZER_SECTIONS = [", 1)[1].split("\n]\n", 1)[0]

    rendered = {}
    for key in app_module.ARENA_AVATAR_OPTIONS:
        field = re.search(rf"\['{key}', '[^']+', (\[\[.*?\]\])", catalog, re.S)
        assert field, f"the locker has no {key} field"
        rendered[key] = {value for value in re.findall(r"\['([a-z_]+)',", field.group(1))}

    assert rendered == {key: set(values) for key, values in app_module.ARENA_AVATAR_OPTIONS.items()}

    defaults = source.split("ARENA_AVATAR_DEFAULT = {", 1)[1].split("}", 1)[0]
    assert dict(re.findall(r"(\w+): '([\w]+)'", defaults)) == app_module.ARENA_AVATAR_DEFAULT
    # Every default has to be a value the locker actually offers.
    for key, value in app_module.ARENA_AVATAR_DEFAULT.items():
        assert value in app_module.ARENA_AVATAR_OPTIONS[key]


def test_every_rank_bot_has_a_loadout_the_renderer_can_draw():
    """A typo in a bot's loadout is invisible: it just silently defaults.

    Each rank bot is meant to look unmistakably different from the last, so
    every value it names is checked against the same allow-list a student's
    saved loadout goes through.
    """
    source = (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")
    block = source.split("bot_loadouts = {", 1)[1].split("\n        }", 1)[0]
    loadouts = dict(re.findall(r"'(\w+)': \{(.*?)\},", block))
    assert set(loadouts) == {key for _minimum, _label, key in app_module.SAT_BATTLE_RANKS}

    for rank, body in loadouts.items():
        for key, value in re.findall(r"'(\w+)': '(\w+)'", body):
            assert key in app_module.ARENA_AVATAR_OPTIONS, f"{rank} sets unknown slot {key}"
            assert value in app_module.ARENA_AVATAR_OPTIONS[key], f"{rank}.{key} cannot be drawn: {value}"

    # No two ranks should walk out looking like the same fighter.
    rendered = [app_module._normalize_arena_avatar(dict(re.findall(r"'(\w+)': '(\w+)'", body)))
                for body in loadouts.values()]
    assert len({tuple(sorted(avatar.items())) for avatar in rendered}) == len(rendered)


def test_every_bank_question_declares_the_section_it_belongs_to():
    """The calculator is offered per question, so every item must say which
    section it is. Inferring this from the text misfires: a Punctuation item
    quoting a date reads as Math, and a word problem's answer choices are
    prose. The bank therefore declares it rather than being guessed at."""
    for tier, bank in app_module.SAT_BATTLE_QUESTION_BANK.items():
        for question in bank:
            assert question.get("domain") in {"math", "reading_writing"}, f"{tier}: {question['skill']}"
        # Every tier has to offer both sections, or a fallback round turns into
        # a single-subject drill.
        domains = {question["domain"] for question in bank}
        assert domains == {"math", "reading_writing"}, tier


def test_active_round_tells_the_client_which_questions_get_a_calculator(tmp_path, monkeypatch):
    database = DatabaseHandler(str(tmp_path / "calculator-round.db"))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()
    challenger = _user(database, "calc@example.test", "Calc")
    train = inspect.unwrap(app_module.train_with_sat_battle_bot)

    with app_module.app.test_request_context("/api/sat-battles/train", method="POST", json={"rank": "gold"}):
        round_payload = train(challenger).get_json()

    questions = round_payload["questions"]
    assert len(questions) == app_module.SAT_BATTLE_QUESTION_COUNT
    assert {question["domain"] for question in questions} <= {"math", "reading_writing"}
    assert any(question["domain"] == "math" for question in questions)
    # Domain says which section an item is, and nothing more: the answer key
    # must not have ridden along with it.
    assert all("correct_option" not in question for question in questions)
    assert all("explanation" not in question for question in questions)


def test_desmos_is_framed_rather_than_scripted_into_the_page():
    """Desmos runs in a frame, not as a script in this origin.

    A third-party script tag would execute alongside the session cookie and the
    CSRF token; a frame can only draw graphs. If someone ever relaxes
    script-src to load the Desmos JS API, this is the test that should stop it.
    """
    with app_module.app.test_request_context("/"):
        response = app_module.add_security_headers(app_module.app.make_response("ok"))
    policy = dict(
        (part.strip().split(" ", 1) + [""])[:2]
        for part in response.headers["Content-Security-Policy"].split(";") if part.strip()
    )
    assert policy["frame-src"] == app_module.DESMOS_EMBED_ORIGIN
    assert "desmos" not in policy["script-src"]
    assert policy["script-src"].startswith("'self'")
    assert "desmos" not in policy["connect-src"]


# --- Difficulty actually scaling with rank ---------------------------------

_EASY_MATH = (
    "A gym charges a one-time $20 joining fee plus $9 for each visit. The total cost, in dollars, "
    "for v visits is given by c(v) = 20 + 9v. What does c(6) represent in this situation?"
)
# Base-valid, but it reaches for structure a Bronze student should not meet.
_TOO_HARD_FOR_BRONZE = (
    "For a constant k, the equation x^2 - 6x + k = 0 has exactly one real solution, and the "
    "discriminant of a second equation x^2 - 2kx + 9 = 0 is also zero. What is the sum of all "
    "possible values of k that satisfy both conditions for all real x?"
)
_BRONZE_MATH = {
    0: _EASY_MATH,
    1: ("A survey of 200 students found that 130 of them ride the bus to school. Based on the "
        "survey, what percent of the students ride the bus to school?"),
    2: ("A rectangular garden is 12 feet long and 7 feet wide. A gardener adds a path of uniform "
        "width around the outside of the garden. If the distance across the garden and both "
        "sections of path is 18 feet, how wide is the path?"),
}
_BRONZE_READING = {
    3: ("Marine biologist Dana Okoro studied a reef where corals had been bleached two years "
        "earlier. She recorded that fish species which feed on algae returned to the reef sooner "
        "than species that shelter among branching corals. Okoro also noted that branching corals "
        "regrow more slowly after bleaching than other coral types do. Which conclusion is best "
        "supported by the text?"),
    4: ("A reviewer praised the museum's new audio guide as unhurried, noting that it pauses "
        "between descriptions so that visitors can look closely at each object before moving on "
        "to the next one. As used in the text, unhurried most nearly means"),
}


def _bronze_item(slot, *, math_text=None):
    if slot < 3:
        return {
            "domain": "math",
            "question_text": math_text or _BRONZE_MATH[slot],
            "options": [f"Bronze {slot} choice {letter}" for letter in "ABCD"],
            "correct_option": slot % 4,
            "skill": f"Bronze math skill {slot}",
            "explanation": "The key follows directly from the one setup step; the tempting wrong choice reverses it.",
        }
    return {
        "domain": "reading_writing",
        "question_text": _BRONZE_READING[slot],
        "options": [f"Bronze {slot} choice {letter}" for letter in "ABCD"],
        "correct_option": slot % 4,
        "skill": f"Bronze reading skill {slot}",
        "explanation": "The key stays inside what the paragraph states; the tempting wrong choice overstates it.",
    }


def test_difficulty_bands_climb_with_every_rank():
    """The ladder has to be a ladder.

    Before this table existed, tier difficulty lived entirely in prose sent to
    the model and nothing checked the result, so a Bronze round could carry
    Diamond questions and nobody would know.
    """
    tiers = [key for _minimum, _label, key in reversed(app_module.SAT_BATTLE_RANKS)]
    specs = [app_module.SAT_BATTLE_TIER_CONTRACT[tier] for tier in tiers]
    assert len(specs) == len(app_module.SAT_BATTLE_RANKS)

    for lower, higher, pair in zip(specs, specs[1:], zip(tiers, tiers[1:])):
        assert lower["math"][0] < higher["math"][0], pair
        assert lower["math"][1] < higher["math"][1], pair
        assert lower["words"][0] < higher["words"][0], pair
        assert lower["words"][1] < higher["words"][1], pair
        assert lower["layers"][0] <= higher["layers"][0], pair
        assert lower["layers"][1] < higher["layers"][1], pair
        # Upper-tier structure unlocks once and never locks again.
        assert higher["advanced"] >= lower["advanced"], pair
        assert higher["paired"] >= lower["paired"], pair

    assert specs[0]["advanced"] is False and specs[-1]["advanced"] is True
    assert specs[0]["paired"] is False and specs[-1]["paired"] is True


def test_an_easy_item_is_bronze_only_and_a_layered_one_is_not_bronze():
    """The bands have to exclude each other, not merely differ on paper."""
    easy = {"question_text": _EASY_MATH, "domain": "math"}
    layered = {"question_text": _TOO_HARD_FOR_BRONZE, "domain": "math"}

    assert app_module._battle_tier_contract_failure(easy, 0, "bronze") is None
    for tier in ("diamond", "master", "grandmaster"):
        assert app_module._battle_tier_contract_failure(easy, 0, tier), tier

    assert app_module._battle_tier_contract_failure(layered, 0, "bronze")
    assert app_module._battle_tier_contract_failure(layered, 0, "silver")

    # A wall of text is not difficulty: an over-long Bronze stem is rejected too.
    padded = {"question_text": _EASY_MATH + " " + "Additional context. " * 40, "domain": "math"}
    assert "ceiling" in app_module._battle_tier_contract_failure(padded, 0, "bronze")


def test_bronze_regenerates_a_slot_that_drifted_above_its_tier(tmp_path, monkeypatch):
    _arena_database(tmp_path, monkeypatch, "bronze-band.db")
    script = {slot: [_bronze_item(slot)] for slot in range(5)}
    script[0] = [_bronze_item(0, math_text=_TOO_HARD_FOR_BRONZE), _bronze_item(0)]
    generate, calls = _arena_generator(script)
    monkeypatch.setattr(app_module, "_generate_text", generate)

    questions = app_module._battle_questions(1000)

    assert {question["difficulty"] for question in questions} == {"bronze"}
    assert questions[0]["question_text"] == _EASY_MATH
    # Only the drifting slot was rewritten.
    slots_written = [int(re.search(r"Slot: (\d) of 5", call).group(1)) for call in calls if "Slot:" in call]
    assert sorted(slots_written) == [1, 1, 2, 3, 4, 5]
    # Bronze is not audited, so no second model pass was spent on it.
    assert not any("Independently audit" in call for call in calls)


def test_each_tier_prompt_states_the_band_its_gate_will_measure(tmp_path, monkeypatch):
    """A gate the writer is never told about is just a slower failure."""
    _arena_database(tmp_path, monkeypatch, "band-prompts.db")
    for tier, rating in (("bronze", 1000), ("grandmaster", 1750)):
        script = {slot: [_bronze_item(slot) for _ in range(4)] for slot in range(5)}
        generate, calls = _arena_generator(script)
        monkeypatch.setattr(app_module, "_generate_text", generate)
        app_module._battle_questions(rating)

        contract = app_module.SAT_BATTLE_TIER_CONTRACT[tier]
        math_call = next(call for call in calls if "Slot: 1 of 5" in call)
        reading_call = next(call for call in calls if "Slot: 4 of 5" in call)
        assert f"between {contract['math'][0]} and {contract['math'][1]} characters" in math_call
        assert f"chain {contract['layers'][0]}-{contract['layers'][1]}" in math_call
        assert f"{contract['words'][0]}-{contract['words'][1]} words" in reading_call
        # Bronze is told what it may not reach for; Grandmaster is not held back.
        banned = "Do not use discriminants" in math_call
        assert banned is (not contract["advanced"])


# --- Rating ----------------------------------------------------------------

def test_elo_pays_for_the_opponent_you_actually_beat():
    """The flat +24/-14 this replaced let the ladder be farmed at the bottom."""
    # An upset is worth far more than beating an equal, and costs the favourite.
    assert app_module._elo_delta(1000, 1750, "win", 25) > app_module._elo_delta(1000, 1000, "win", 25)
    assert app_module._elo_delta(1750, 1000, "win", 25) < app_module._elo_delta(1000, 1000, "win", 25)
    assert app_module._elo_delta(1000, 1750, "loss", 25) > app_module._elo_delta(1000, 1000, "loss", 25)

    # A win never costs rating and a loss never pays, however lopsided.
    for mine, theirs in ((800, 2000), (2000, 800), (1000, 1000)):
        assert app_module._elo_delta(mine, theirs, "win", 25) > 0
        assert app_module._elo_delta(mine, theirs, "loss", 25) < 0

    # Even opponents at equal K are zero sum, so draws stop inflating the ladder.
    assert app_module._elo_delta(1200, 1200, "draw", 25) == 0
    winner = app_module._elo_delta(1200, 1400, "win", 25)
    loser = app_module._elo_delta(1400, 1200, "loss", 25)
    assert winner + loser == 0

    # Placement rounds move faster than a settled rating.
    assert app_module._elo_k_factor(0, 1000) > app_module._elo_k_factor(50, 1000)
    assert app_module._elo_k_factor(50, 1600) < app_module._elo_k_factor(50, 1000)


def test_bot_rounds_are_worth_what_the_bots_tier_is_worth():
    """Beating the Grandmaster bot has to outrank beating the Bronze one.

    Bronze's ladder threshold is 0, and a bot rated 0 would pay nothing to beat
    and wreck a rating to lose to, so the floor matters here.
    """
    tiers = [key for _minimum, _label, key in reversed(app_module.SAT_BATTLE_RANKS)]
    ratings = [app_module._battle_tier_rating(tier) for tier in tiers]
    assert ratings == sorted(ratings)
    assert min(ratings) >= app_module.SAT_BATTLE_BASE_RATING

    gains = [app_module._elo_delta(1000, rating, "win", 25) for rating in ratings]
    assert gains == sorted(gains)
    assert gains[-1] > gains[0]


def test_a_ranked_round_moves_both_ladders_and_reports_the_swing(tmp_path, monkeypatch):
    database = DatabaseHandler(str(tmp_path / "elo-round.db"))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()
    winner = _user(database, "elo-win@example.test", "Winner")
    loser = _user(database, "elo-lose@example.test", "Loser")
    database.insert("sat_battle_stats", {
        "user_id": loser.data["id"], "user_name": "Loser", "rating": 1600,
        "wins": 0, "losses": 0, "draws": 0, "battles_played": 40,
    })
    queue = inspect.unwrap(app_module.queue_sat_battle)
    submit = inspect.unwrap(app_module.submit_sat_battle)

    with app_module.app.test_request_context("/api/sat-battles/queue", method="POST", json={}):
        queue(winner)
    with app_module.app.test_request_context("/api/sat-battles/queue", method="POST", json={}):
        active = queue(loser).get_json()

    key = [question["correct_option"] for question in json.loads(
        database.select_one("sat_battles", where={"id": active["id"]})["questions"])]
    right = [{"question_index": i, "selected_option": option} for i, option in enumerate(key)]
    wrong = [{"question_index": i, "selected_option": (option + 1) % 4} for i, option in enumerate(key)]

    with app_module.app.test_request_context(f"/api/sat-battles/{active['id']}/submit", method="POST", json={"answers": right}):
        submit(winner, active["id"])
    with app_module.app.test_request_context(f"/api/sat-battles/{active['id']}/submit", method="POST", json={"answers": wrong}):
        result = submit(loser, active["id"]).get_json()

    winner_stats = database.select_one("sat_battle_stats", where={"user_id": winner.data["id"]})
    loser_stats = database.select_one("sat_battle_stats", where={"user_id": loser.data["id"]})
    assert winner_stats["rating"] > app_module.SAT_BATTLE_BASE_RATING
    assert loser_stats["rating"] < 1600
    assert winner_stats["wins"] == 1 and loser_stats["losses"] == 1

    # Beating a 1600 from an unrated start is a real upset, not a flat bump.
    assert winner_stats["rating"] - app_module.SAT_BATTLE_BASE_RATING > 24
    # The loser sees their own swing, and it is the one that was applied.
    assert result["ratingDelta"] == loser_stats["rating"] - 1600
    assert result["rank"]["rating"] == loser_stats["rating"]
    # The rank held going in is reported too, so the screen can name a demotion
    # rather than leaving the student to compare numbers from memory.
    assert result["previousRank"]["rating"] == 1600
    assert result["previousRank"]["label"] == "Master"


def test_training_rounds_never_touch_the_ladder(tmp_path, monkeypatch):
    database = DatabaseHandler(str(tmp_path / "elo-training.db"))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()
    student = _user(database, "elo-training@example.test", "Student")
    train = inspect.unwrap(app_module.train_with_sat_battle_bot)
    submit = inspect.unwrap(app_module.submit_sat_battle)

    with app_module.app.test_request_context("/api/sat-battles/train", method="POST", json={"rank": "grandmaster"}):
        drill = train(student).get_json()
    key = [question["correct_option"] for question in json.loads(
        database.select_one("sat_battles", where={"id": drill["id"]})["questions"])]
    answers = [{"question_index": i, "selected_option": option} for i, option in enumerate(key)]
    with app_module.app.test_request_context(f"/api/sat-battles/{drill['id']}/submit", method="POST", json={"answers": answers}):
        submit(student, drill["id"])

    assert database.select_one("sat_battle_stats", where={"user_id": student.data["id"]}) is None


def test_the_higher_rank_sets_the_tier_whichever_player_queued_first(tmp_path, monkeypatch):
    """Join order must not decide difficulty.

    Reading the joining player's rating is the easy way to write this and looks
    correct in one direction only, so both orders are pinned.
    """
    database = DatabaseHandler(str(tmp_path / "queue-order.db"))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()
    queue = inspect.unwrap(app_module.queue_sat_battle)

    for first, second in (("waits", "joins"), ("joins", "waits")):
        strong = _user(database, f"strong-{first}@example.test", "Strong")
        weak = _user(database, f"weak-{first}@example.test", "Weak")
        database.insert("sat_battle_stats", {
            "user_id": strong.data["id"], "user_name": "Strong", "rating": 1750,
            "wins": 0, "losses": 0, "draws": 0, "battles_played": 0,
        })
        order = (strong, weak) if first == "waits" else (weak, strong)
        with app_module.app.test_request_context("/api/sat-battles/queue", method="POST", json={}):
            queue(order[0])
        with app_module.app.test_request_context("/api/sat-battles/queue", method="POST", json={}):
            active = queue(order[1]).get_json()

        assert active["status"] == "active"
        assert active["difficulty"] == "grandmaster", f"{first} queued first"
        database.update("sat_battles", {"status": "expired"}, where={"id": active["id"]})


# --- Daily streak ----------------------------------------------------------

def test_a_streak_expires_when_the_student_stops(tmp_path, monkeypatch):
    """The stored counter is only written on a completion, so nothing ever
    reset it. A student who last studied weeks ago kept seeing that number on
    their dashboard, which is the one thing a streak must never get wrong."""
    from datetime import date, timedelta
    today = date(2026, 3, 14)

    alive_today = {"current_streak": 6, "last_completed_date": today.isoformat()}
    alive_yesterday = {"current_streak": 6, "last_completed_date": (today - timedelta(days=1)).isoformat()}
    stale = {"current_streak": 6, "last_completed_date": (today - timedelta(days=2)).isoformat()}
    ancient = {"current_streak": 41, "last_completed_date": (today - timedelta(days=30)).isoformat()}

    assert app_module._live_streak(alive_today, today) == 6
    # Yesterday still counts: today is not over yet.
    assert app_module._live_streak(alive_yesterday, today) == 6
    assert app_module._live_streak(stale, today) == 0
    assert app_module._live_streak(ancient, today) == 0

    # Missing or unreadable dates cannot be treated as a live streak.
    assert app_module._live_streak({"current_streak": 9}, today) == 0
    assert app_module._live_streak({"current_streak": 9, "last_completed_date": "nonsense"}, today) == 0
    assert app_module._live_streak(None, today) == 0
    assert app_module._live_streak({}, today) == 0


def test_finishing_a_second_step_the_same_day_does_not_inflate_the_streak(tmp_path, monkeypatch):
    from datetime import date, timedelta
    database = DatabaseHandler(str(tmp_path / "streak.db"))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()
    student = _user(database, "streak@example.test", "Streak")
    user_id = student.data["id"]

    day = date(2026, 3, 10)
    monkeypatch.setattr(app_module, "_user_today", lambda: day)

    def stored():
        return database.select_one("gamification_stats", where={"user_id": user_id})

    app_module._advance_completion_streak(user_id)
    assert stored()["current_streak"] == 1
    # Three more steps on the same day must not buy three more days.
    for _ in range(3):
        app_module._advance_completion_streak(user_id)
    assert stored()["current_streak"] == 1

    for offset in (1, 2, 3):
        monkeypatch.setattr(app_module, "_user_today", lambda offset=offset: day + timedelta(days=offset))
        app_module._advance_completion_streak(user_id)
    assert stored()["current_streak"] == 4

    # A gap restarts at one rather than continuing from the old number.
    monkeypatch.setattr(app_module, "_user_today", lambda: day + timedelta(days=9))
    app_module._advance_completion_streak(user_id)
    assert stored()["current_streak"] == 1


def test_the_streak_day_follows_the_student_not_the_server():
    """An evening session in the Americas is still today for that student."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    with app_module.app.test_request_context("/"):
        from flask import session
        session["timezone"] = "America/Los_Angeles"
        local = app_module._user_today()
    assert local == datetime.now(ZoneInfo("America/Los_Angeles")).date()

    with app_module.app.test_request_context("/"):
        from flask import session
        session["timezone"] = "Not/AZone"
        assert app_module._user_today() == datetime.now(ZoneInfo("UTC")).date()


# --- Battle win streak -----------------------------------------------------

def _ranked_round(database, winner, loser):
    """Play one ranked round to completion and return the loser's payload."""
    queue = inspect.unwrap(app_module.queue_sat_battle)
    submit = inspect.unwrap(app_module.submit_sat_battle)
    with app_module.app.test_request_context("/api/sat-battles/queue", method="POST", json={}):
        queue(winner)
    with app_module.app.test_request_context("/api/sat-battles/queue", method="POST", json={}):
        active = queue(loser).get_json()
    key = [q["correct_option"] for q in json.loads(
        database.select_one("sat_battles", where={"id": active["id"]})["questions"])]
    right = [{"question_index": i, "selected_option": o} for i, o in enumerate(key)]
    wrong = [{"question_index": i, "selected_option": (o + 1) % 4} for i, o in enumerate(key)]
    with app_module.app.test_request_context(f"/api/sat-battles/{active['id']}/submit", method="POST", json={"answers": right}):
        submit(winner, active["id"])
    with app_module.app.test_request_context(f"/api/sat-battles/{active['id']}/submit", method="POST", json={"answers": wrong}):
        return submit(loser, active["id"]).get_json()


def test_a_win_streak_builds_and_a_loss_ends_it(tmp_path, monkeypatch):
    database = DatabaseHandler(str(tmp_path / "winstreak.db"))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()
    champ = _user(database, "champ@example.test", "Champ")
    rival = _user(database, "rival@example.test", "Rival")

    def streak(user):
        row = database.select_one("sat_battle_stats", where={"user_id": user.data["id"]})
        return (row or {}).get("win_streak") or 0, (row or {}).get("best_win_streak") or 0

    for expected in (1, 2, 3):
        _ranked_round(database, champ, rival)
        assert streak(champ) == (expected, expected)
        # The loser's run stays at zero throughout.
        assert streak(rival) == (0, 0)

    # One loss ends the run, but the best is kept.
    _ranked_round(database, rival, champ)
    assert streak(champ) == (0, 3)
    assert streak(rival) == (1, 1)

    # Rebuilding does not forget the old best until it is beaten.
    _ranked_round(database, champ, rival)
    assert streak(champ) == (1, 3)


def test_a_drawn_round_ends_a_win_streak(tmp_path, monkeypatch):
    """A streak is a run of wins, so a draw has to end it -- otherwise the
    flame survives rounds nobody actually won."""
    database = DatabaseHandler(str(tmp_path / "draw-streak.db"))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()
    player = _user(database, "drawer@example.test", "Drawer")
    database.insert("sat_battle_stats", {
        "user_id": player.data["id"], "user_name": "Drawer", "rating": 1200,
        "wins": 4, "losses": 0, "draws": 0, "battles_played": 4,
        "win_streak": 4, "best_win_streak": 4,
    })

    app_module._battle_rating(player.data["id"], "Drawer", "draw", 1200)

    row = database.select_one("sat_battle_stats", where={"user_id": player.data["id"]})
    assert row["win_streak"] == 0
    assert row["best_win_streak"] == 4


def test_training_rounds_do_not_touch_the_win_streak(tmp_path, monkeypatch):
    database = DatabaseHandler(str(tmp_path / "training-streak.db"))
    monkeypatch.setattr(app_module, "db", database)
    app_module.init_db()
    student = _user(database, "drill@example.test", "Drill")
    database.insert("sat_battle_stats", {
        "user_id": student.data["id"], "user_name": "Drill", "rating": 1000,
        "wins": 0, "losses": 0, "draws": 0, "battles_played": 0,
        "win_streak": 2, "best_win_streak": 2,
    })
    train = inspect.unwrap(app_module.train_with_sat_battle_bot)
    submit = inspect.unwrap(app_module.submit_sat_battle)

    with app_module.app.test_request_context("/api/sat-battles/train", method="POST", json={"rank": "bronze"}):
        drill = train(student).get_json()
    key = [q["correct_option"] for q in json.loads(
        database.select_one("sat_battles", where={"id": drill["id"]})["questions"])]
    wrong = [{"question_index": i, "selected_option": (o + 1) % 4} for i, o in enumerate(key)]
    with app_module.app.test_request_context(f"/api/sat-battles/{drill['id']}/submit", method="POST", json={"answers": wrong}):
        submit(student, drill["id"])

    row = database.select_one("sat_battle_stats", where={"user_id": student.data["id"]})
    assert row["win_streak"] == 2, "a losing drill must not break a ranked streak"


def test_flame_tiers_climb_without_gaps():
    """Every streak length has exactly one tier, and the tiers only go up."""
    source = (Path(__file__).resolve().parents[1] / "frontend" / "src" / "App.jsx").read_text(encoding="utf-8")
    block = source.split("const WIN_STREAK_TIERS = [", 1)[1].split("\n]", 1)[0]
    tiers = [(int(at), key) for at, key in re.findall(r"at: (\d+), key: '(\w+)'", block)]

    assert len(tiers) >= 5
    assert [at for at, _ in tiers] == sorted(at for at, _ in tiers)
    assert len({key for _, key in tiers}) == len(tiers)
    # The first tier lights on the first win, so there is no dead band.
    assert tiers[0][0] == 1
    # Every tier is reachable: no two thresholds collide.
    assert len({at for at, _ in tiers}) == len(tiers)
