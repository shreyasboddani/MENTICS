"""The plan contract: server-owned usable nodes no matter what the model returns.

_complete_five_step_plan enforced this when a single call produced the whole
path. The server now owns the unit shape, so the same guarantee lives in the
plan normalizers, and these tests hold them to it.
"""

import learning


TEST_PROFILE = {
    "weaknesses": "vocabulary, quadratic functions",
    "focus": "sat",
    "skill_options": learning.skill_catalog("sat"),
    "_mastery_rows": [],
}

COLLEGE_PROFILE = {
    "stage": "applying",
    "skill_options": learning.college_skill_options("applying"),
    "milestone": learning.COLLEGE_MILESTONES["applying"],
}


def _test_plan(raw):
    return learning._normalize_plan(raw, learning.CANONICAL_SHAPE, dict(TEST_PROFILE))


def test_plan_holds_the_shape_when_the_model_returns_nothing():
    plan = _test_plan({})

    assert [node["node_type"] for node in plan["nodes"]] == learning.CANONICAL_SHAPE
    assert all(node["skill"]["skill_key"] for node in plan["nodes"])
    assert all(node["objective"] and node["reason"] for node in plan["nodes"])


def test_plan_survives_malformed_and_missing_nodes():
    plan = _test_plan({"nodes": [
        {"skill_key": "words_in_context", "title": "Words in Context"},
        None,
        {"skill_key": "", "syllabus": ["too short"]},
        "not an object",
    ]})

    assert len(plan["nodes"]) == 5
    assert all(len(node["syllabus"]) >= 2 for node in plan["nodes"]
               if node["node_type"] not in ("boss_battle", "milestone"))


def test_plan_does_not_teach_the_same_skill_in_both_lessons():
    plan = _test_plan({"nodes": [
        {"skill_key": "words_in_context"},
        {"skill_key": "words_in_context"},
        {"skill_key": "words_in_context"},
        {"skill_key": "words_in_context"},
    ]})

    lessons = [n["skill"]["skill_key"] for n in plan["nodes"] if n["node_type"] == "lesson"]
    assert len(set(lessons)) == len(lessons)


def test_drill_reinforces_the_lesson_before_it():
    plan = _test_plan({"nodes": [{"skill_key": "transitions"}, {}, {}, {}]})
    nodes = plan["nodes"]

    assert nodes[0]["node_type"] == "lesson"
    assert nodes[1]["node_type"] == "practice_sprint"
    assert nodes[1]["skill"]["skill_key"] == nodes[0]["skill"]["skill_key"]


def test_review_never_introduces_an_untaught_skill():
    plan = _test_plan({"nodes": [{"skill_key": "boundaries"}, {}, {"skill_key": "transitions"}, {}]})
    taught = {n["skill"]["skill_key"] for n in plan["nodes"] if n["node_type"] in ("lesson", "practice_sprint")}
    quiz = next(n for n in plan["nodes"] if n["node_type"] == "quiz")

    assert quiz["skill"]["skill_key"] in taught


def test_an_invented_skill_key_still_resolves_to_a_real_skill():
    plan = _test_plan({"nodes": [{"skill_key": "made_up_nonsense", "title": "quadratic equations"}]})

    assert plan["nodes"][0]["skill"]["skill_key"] in learning.SKILL_TAXONOMY


def test_college_plan_is_a_lesson_then_a_real_world_deliverable():
    plan = learning._normalize_college_plan({}, learning.COLLEGE_SHAPE, dict(COLLEGE_PROFILE))

    assert [node["node_type"] for node in plan["nodes"]] == learning.COLLEGE_SHAPE
    milestone = plan["nodes"][-1]
    assert milestone["node_type"] == "milestone"
    assert milestone["stat_to_update"] == "applications_submitted"
    assert all(node["skill"]["skill_key"] in learning.COLLEGE_TAXONOMY for node in plan["nodes"])
    assert plan["nodes"][0]["node_type"] == "lesson"
    assert "report back" in milestone["reason"].lower()


def test_college_unit_never_generates_multiple_choice_checks(monkeypatch):
    monkeypatch.setattr(learning, "plan_college_unit", lambda *_: {})
    monkeypatch.setattr(learning, "generate_college_teaching", lambda node, profile: {
        "intro": "A direct lesson.",
        "cards": [{"title": "One useful idea", "body": "Concrete guidance for a real application decision.",
                   "worked_example": "A real example.", "takeaway": "Use it today.", "trap": "Being vague."}],
        "recap": "Use the idea in the assignment.",
    })
    unit = learning.build_college_unit(dict(COLLEGE_PROFILE))

    assert [node["node_type"] for node in unit["nodes"]] == ["lesson", "milestone"]
    assert all(step["step_type"] != "check" for step in unit["nodes"][0]["steps"])
