from learning import _fallback_teaching


def _node(subject="Math", syllabus=None):
    return {
        "skill": {
            "subject": subject,
            "skill_label": "Quadratic graph transformations",
        },
        "objective": "Distinguish horizontal and vertical shifts in vertex form.",
        "syllabus": syllabus if syllabus is not None else [
            "Read vertex form",
            "Identify horizontal shifts",
            "Identify vertical shifts",
            "Check the transformed graph",
        ],
    }


def test_fallback_teaching_is_complete_enough_to_use():
    lesson = _fallback_teaching(_node())

    assert lesson["intro"]
    assert lesson["recap"]
    assert len(lesson["cards"]) == 4
    for card in lesson["cards"]:
        assert card["title"]
        assert card["body"]
        assert card["worked_example"]
        assert card["takeaway"]
        assert card["trap"]


def test_fallback_teaching_preserves_task_specific_content():
    lesson = _fallback_teaching(_node())
    content = " ".join(
        [lesson["intro"], lesson["recap"]]
        + [value for card in lesson["cards"] for value in card.values()]
    ).lower()

    assert "quadratic graph transformations" in content
    assert "vertex form" in content
    assert "horizontal shifts" in content
    assert "vertical shifts" in content


def test_fallback_teaching_handles_an_empty_syllabus():
    lesson = _fallback_teaching(_node(syllabus=[]))

    assert len(lesson["cards"]) == 1
    assert lesson["cards"][0]["title"] == "Quadratic graph transformations"
