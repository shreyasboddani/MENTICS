def _get_current_numbered_tasks(user_id, category):
    """Helper function to get current active tasks with numbering for a specific category."""
    latest_task_query = """
        SELECT created_at FROM paths
        WHERE user_id=? AND category=? AND is_active=True
        ORDER BY created_at DESC LIMIT 1
    """
    latest_task_timestamp_result = db.execute(
        latest_task_query, (user_id, category))

    if not latest_task_timestamp_result:
        return "No active tasks at the moment."

    latest_timestamp = latest_task_timestamp_result[0]['created_at']
    active_tasks = db.select(
        "paths",
        where={
            "user_id": user_id,
            "is_active": True,
            "category": category,
            "created_at": latest_timestamp
        }
    )

    if not active_tasks:
        return "No active tasks at the moment."

    # Sort by task_order and create numbered list
    active_tasks = sorted(active_tasks, key=lambda x: x['task_order'])
    numbered_tasks = []
    for i, task in enumerate(active_tasks, 1):
        status = "✅ (Completed)" if task['is_completed'] else "⏳ (In Progress)"
        numbered_tasks.append(f"Task {i}: {task['description']} - {status}")

    return "\n".join(numbered_tasks)
