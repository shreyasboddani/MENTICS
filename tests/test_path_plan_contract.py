from app import _complete_five_step_plan


def test_path_plan_contract_keeps_only_five_distinct_tasks():
    repeated = [
        {"description": "Master vocabulary in context with a focused Digital SAT practice sprint", "reason": "Vocabulary is a stated weakness."},
        {"description": "Practice Digital SAT vocabulary in context in a focused sprint", "reason": "Vocabulary is a stated weakness."},
    ]
    distinct = [
        {"description": f"Complete distinct skill drill {number} with written reflection", "reason": "It targets a separate gap."}
        for number in range(1, 9)
    ]

    tasks = _complete_five_step_plan(repeated + distinct, "Test Prep")

    assert len(tasks) == 5
    descriptions = [task["description"] for task in tasks]
    assert descriptions.count(repeated[0]["description"]) == 1
    assert repeated[1]["description"] not in descriptions
    assert all(task["category"] == "Test Prep" for task in tasks)


def test_path_plan_contract_fills_invalid_or_short_ai_output():
    tasks = _complete_five_step_plan([
        {"description": "Analyze linear equations", "reason": ""},
        None,
        {"description": ""},
    ], "Test Prep")

    assert len(tasks) == 5
    assert all(task["description"] for task in tasks)
    assert all(task["reason"] for task in tasks)

