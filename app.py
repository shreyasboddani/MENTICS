from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dbhelper import DatabaseHandler
from userhelper import User
from functools import wraps
import json
import openai
import os
from dotenv import load_dotenv
import random
from pathlib import Path
# NEW: Import datetime and timedelta to handle dates and session timeout
from datetime import datetime, timedelta

# Explicitly load the .env file from the correct path
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.url_map.strict_slashes = False
app.permanent_session_lifetime = timedelta(
    minutes=10)  # Set session timeout to 10 minutes

db = DatabaseHandler("users.db")

# To use the live API, uncomment the line below
# openai.api_key = os.getenv("OPENAI_API_KEY")

# --- DATABASE INITIALIZATION ---


def init_db():
    db.create_table("users", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "email": "TEXT NOT NULL UNIQUE",
        "password": "TEXT NOT NULL",
        "stats": "TEXT NOT NULL"
    })
    db.create_table("paths", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id": "INTEGER NOT NULL",
        "task_order": "INTEGER NOT NULL",
        "description": "TEXT NOT NULL",
        "is_completed": "BOOLEAN DEFAULT FALSE",
        "is_active": "BOOLEAN DEFAULT TRUE",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "type": "TEXT",
        "stat_to_update": "TEXT",
        "category": "TEXT DEFAULT 'Test Prep'"
    })

# --- DECORATORS ---


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# --- AI HELPER FUNCTIONS ---


def _get_test_prep_ai_tasks(strengths, weaknesses, user_stats={}, chat_history=[], path_history={}):
    """Generates test preparation tasks with a hyper-detailed prompt for maximum reliability."""

    def get_mock_tasks_reliably():
        # This mock data generator remains your fallback for testing
        print("--- DEBUG: Running mock generator with categories. ---")
        test_prep_tasks = [
            {"description": "Focus on circle theorems.", "type": "standard",
                "stat_to_update": None, "category": "Test Prep"},
            {"description": "Complete a timed SAT Math section and record your score in the chat.",
                "type": "milestone", "stat_to_update": "sat_math", "category": "Test Prep"}
        ]
        college_tasks = [
            {"description": "Brainstorm ideas for your personal essay.",
                "type": "standard", "stat_to_update": None, "category": "College Planning"},
            {"description": "Finalize your college list and categorize schools.",
                "type": "milestone", "stat_to_update": None, "category": "College Planning"}
        ]
        final_tasks = random.sample(
            test_prep_tasks, 2) + random.sample(college_tasks, 2)
        final_tasks.append({"description": "Review 20 new vocabulary words.",
                           "type": "standard", "stat_to_update": None, "category": "Test Prep"})
        random.shuffle(final_tasks)
        return final_tasks

    if not hasattr(openai, 'api_key') or not openai.api_key:
        return get_mock_tasks_reliably()

    # --- DATA FORMATTING FOR THE PROMPT ---
    completed_tasks_str = "\n".join(
        [f"- {task[3]}" for task in path_history.get('completed', [])]) or "None."
    incomplete_tasks_str = "\n".join(
        [f"- {task[3]}" for task in path_history.get('incomplete', [])]) or "None."

    days_left = "Not set"
    test_date_str = user_stats.get("test_path", {}).get("test_date")
    if test_date_str:
        try:
            delta = datetime.strptime(
                test_date_str, '%Y-%m-%d') - datetime.now()
            days_left = f"{delta.days} days remaining"
        except ValueError:
            days_left = "Invalid date format"

    # --- NEW HYPER-DETAILED PROMPT ---
    prompt = (
        f"# CONTEXT\n"
        f"You are an expert AI test prep (SAT & ACT) coach creating a study plan for a high school student.\n"
        f"The student's test is in: {days_left}.\n\n"

        f"# STUDENT PROFILE\n"
        f"- Strengths: {strengths}\n"
        f"- Weaknesses: {weaknesses}\n"
        f"- Current GPA: {user_stats.get('gpa', 'N/A')}\n\n"

        f"# STUDENT HISTORY\n"
        f"## Recently Completed Tasks:\n{completed_tasks_str}\n\n"
        f"## Recently Incomplete or Failed Tasks:\n{incomplete_tasks_str}\n\n"

        f"# YOUR TASK\n"
        f"Generate a new, 5-step study plan based on all the context provided.\n\n"

        f"# CRITICAL RULES\n"
        f"- Your ENTIRE output must be a single, raw JSON object. Do not include any text, explanations, or markdown formatting like ```json before or after the JSON.\n"
        f"- The plan must contain exactly 5 task objects.\n"
        f"- The tasks must be novel. DO NOT repeat any tasks from the student's history.\n"
        f"- The plan must logically progress the student forward from their previous tasks.\n"
        f"- The plan must be appropriate for the time remaining before the test ({days_left}).\n"
        f"- Create a list of appropriate 'Test Prep' tasks if applicable, otherwise focus on the student's stated weaknesses.\n\n"

        f"# JSON SCHEMA\n"
        f"Your output must conform to this exact structure:\n"
        f"{{\n"
        f'  "tasks": [\n'
        f'    {{\n'
        f'      "description": "A string describing the specific, actionable task.",\n'
        f'      "type": "A string, either \'standard\' or \'milestone\'.",\n'
        f'      "stat_to_update": "A string if type is \'milestone\' (must be one of [\'sat_math\', \'sat_ebrw\', \'act_math\', \'act_reading\', \'act_science\', \'gpa\']), otherwise null.",\n'
        f'      "category": "A string, either \'Test Prep\' or \'College Planning\'."\n'
        f'    }},\n'
        f'    ...\n'
        f'  ]\n'
        f'}}'
    )

    try:
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that responds only in perfectly formatted JSON based on the user's instructions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        response_data = json.loads(completion.choices[0].message.content)
        tasks = response_data.get("tasks", [])
        if isinstance(tasks, list) and len(tasks) == 5:
            return tasks
        raise ValueError("Invalid format from AI")
    except Exception as e:
        print(f"\n--- OPENAI API ERROR IN _get_test_prep_ai_tasks: {e} ---\n")
        return get_mock_tasks_reliably()


def _get_test_prep_ai_chat_response(history, user_stats):
    if not hasattr(openai, 'api_key') or not openai.api_key:
        return "I'm in testing mode, but I'm saving our conversation!"

    # NEW: Add test date context to chat
    days_left = "a future date"
    test_date_str = user_stats.get("test_path", {}).get("test_date")
    if test_date_str:
        try:
            test_date = datetime.strptime(test_date_str, '%Y-%m-%d')
            delta = test_date - datetime.now()
            days_left = f"{delta.days} days"
        except ValueError:
            pass  # Ignore invalid date format in chat

    # NEW: Proactive and context-aware system prompt
    system_message = {
        "role": "system",
        "content": (
            "You are a friendly and proactive study coach. Your student's test is in "
            f"{days_left}. If the conversation history is empty, greet the user, "
            "remind them of their test date, and ask what they'd like to focus on. "
            "In subsequent messages, be an encouraging tutor. Acknowledge scores and struggles."
        )
    }

    messages = [system_message] + history
    try:
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo", messages=messages)
        return completion.choices[0].message.content
    except Exception as e:
        print(
            f"\n--- OPENAI API ERROR IN _get_test_prep_ai_chat_response: {e} ---\n")
        return "Sorry, I encountered an error connecting to the AI."


def _generate_and_save_new_test_path(user_id, strengths, weaknesses):
    user_record = db.select("users", where={"id": user_id})
    user_stats = json.loads(user_record[0][3]) if user_record else {}
    chat_history = session.get('chat_history', [])

    # NEW: Fetch and process the user's entire path history
    all_tasks = db.select("paths", where={"user_id": user_id})
    path_history = {
        # is_completed is column 4
        "completed": [task for task in all_tasks if task[4]],
        "incomplete": [task for task in all_tasks if not task[4]]
    }

    db.update("paths", {"is_active": False}, where={"user_id": user_id})

    # Pass all context to the AI
    tasks = _get_test_prep_ai_tasks(strengths, weaknesses,
                                    user_stats, chat_history, path_history)

    saved_tasks = []
    for i, task in enumerate(tasks):
        task_id = db.insert("paths", {
            "user_id": user_id,
            "task_order": i + 1,
            "description": task.get("description"),
            "type": task.get("type"),
            "stat_to_update": task.get("stat_to_update"),
            # Default to Test Prep if not specified
            "category": task.get("category", "Test Prep"),
            "is_active": True,
            "is_completed": False
        })
        new_task_data = db.select("paths", where={"id": task_id})[0]
        saved_tasks.append({
            "id": new_task_data[0],
            "description": new_task_data[3],
            "type": new_task_data[7],
            "stat_to_update": new_task_data[8],
            "is_completed": False
        })
    return saved_tasks

# --- ORIGINAL PAGE ROUTES (Unchanged) ---


@app.route("/")
def home():
    is_logged_in = "user" in session
    return render_template("index.html", is_logged_in=is_logged_in)

# Signup route


@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        try:
            user_id = db.insert("users", {
                "email": email,
                "password": password,
                "stats": json.dumps({
                    "sat_ebrw": "",
                    "sat_math": "",
                    "act_math": "",
                    "act_reading": "",
                    "act_science": "",
                    "gpa": "",
                    "milestones": 0
                })
            })
            # Automatically log in the user after successful signup
            session["user"] = email
            session["user_id"] = user_id
            session.permanent = True  # Enable permanent session
            return redirect(url_for("dashboard"))
        except Exception as e:
            print(f"Signup error: {e}")
            error = "Email already exists!"
    return render_template("signup.html", error=error)

# Login route


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    # If user is already logged in, redirect to dashboard
    if "user" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = db.select("users", where={"email": email})
        if user and check_password_hash(user[0][2], password):
            session["user"] = user[0][1]
            session["user_id"] = user[0][0]  # Store user_id in session
            session.permanent = True  # Enable session timeout
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid credentials"
    return render_template("login.html", error=error)

# Dashboard page


@app.route("/dashboard")
@login_required
def dashboard():
    user = User.from_session(db, session)
    if not user:
        return redirect(url_for("login"))
    stats = user.get_stats()
    user_id = user.data[0]

    # Get all tasks for the user
    all_user_tasks = db.select("paths", where={"user_id": user_id})

    # Get active Test Prep tasks for current generation
    active_tasks = [task for task in all_user_tasks
                    # is_active is True and category is Test Prep
                    if task[5] and task[9] == 'Test Prep']

    # Count completed tasks in current generation (out of 5 total tasks)
    test_prep_completed = sum(
        1 for task in active_tasks if task[4])  # is_completed

    # Count total completed tasks across ALL generations
    total_test_prep_completed = sum(
        1 for task in all_user_tasks
        # is_completed and category is Test Prep
        if task[4] and task[9] == 'Test Prep'
    )

    # Keep college planning as is for now
    college_planning_completed = sum(
        1 for task in all_user_tasks
        if task[4] and task[9] == 'College Planning'
    )
    college_planning_upcoming = sum(
        1 for task in all_user_tasks
        if not task[4] and task[5] and task[9] == 'College Planning'
    )

    return render_template(
        "dashboard.html",
        test_prep_completed=test_prep_completed,
        total_test_prep_completed=total_test_prep_completed,
        college_planning_completed=college_planning_completed,
        college_planning_upcoming=college_planning_upcoming,
        gpa=stats.get("gpa", "")
    )


# In app.py, replace the existing /dashboard/stats function

@app.route("/dashboard/stats", methods=["GET"])
@login_required
def stats():
    user = User.from_session(db, session)
    if not user:
        return redirect(url_for("login"))
    stats = user.get_stats()
    user_id = user.data[0]

    # Get all tasks for the user
    all_user_tasks = db.select("paths", where={"user_id": user_id})

    # Get active Test Prep tasks for current generation
    active_tasks = [task for task in all_user_tasks
                    # is_active is True and category is Test Prep
                    if task[5] and task[9] == 'Test Prep']

    # Count completed tasks in current generation (out of 5 total tasks)
    test_prep_completed = sum(
        1 for task in active_tasks if task[4])  # is_completed
    # Always 5 total tasks in current generation
    test_prep_upcoming = 5 - test_prep_completed

    # Count total completed tasks across ALL generations
    total_test_prep_completed = sum(
        1 for task in all_user_tasks
        # is_completed and category is Test Prep
        if task[4] and task[9] == 'Test Prep'
    )

    # Keep college planning at 0 for now
    college_planning_completed = 0
    college_planning_upcoming = 0

    return render_template(
        "stats.html",
        test_prep_completed=test_prep_completed,
        test_prep_upcoming=test_prep_upcoming,
        total_test_prep_completed=total_test_prep_completed,
        college_planning_completed=college_planning_completed,
        college_planning_upcoming=college_planning_upcoming,
        gpa=stats.get("gpa", ""),
        sat_ebrw=stats.get("sat_ebrw", ""),
        sat_math=stats.get("sat_math", ""),
        act_math=stats.get("act_math", ""),
        act_reading=stats.get("act_reading", ""),
        act_science=stats.get("act_science", "")
    )


@app.route("/dashboard/stats/edit", methods=["GET", "POST"])
@login_required
def edit_stats():
    user = User.from_session(db, session)
    if not user:
        return redirect(url_for("login"))
    stats = user.get_stats()
    error = None
    if request.method == "POST":
        # Get each field from the form
        sat_ebrw = request.form.get("sat_ebrw", "")
        sat_math = request.form.get("sat_math", "")
        act_math = request.form.get("act_math", "")
        act_reading = request.form.get("act_reading", "")
        act_science = request.form.get("act_science", "")
        gpa = request.form.get("gpa", "")
        try:
            stats["sat_ebrw"] = sat_ebrw
            stats["sat_math"] = sat_math
            stats["act_math"] = act_math
            stats["act_reading"] = act_reading
            stats["act_science"] = act_science
            stats["gpa"] = gpa
            user.set_stats(stats)
            return redirect(url_for("stats"))
        except Exception as e:
            print("Error updating stats:", e)
            error = "Could not update stats."
    # Pass all fields to the template
    return render_template(
        "edit_stats.html",
        sat_ebrw=stats.get("sat_ebrw", ""),
        sat_math=stats.get("sat_math", ""),
        act_math=stats.get("act_math", ""),
        act_reading=stats.get("act_reading", ""),
        act_science=stats.get("act_science", ""),
        gpa=stats.get("gpa", ""),
        error=error
    )


@app.route("/dashboard/tracker")
@login_required
def tracker():
    return render_template("tracker.html")


@app.route("/dashboard/test-path-builder", methods=["GET", "POST"])
@login_required
def test_path_builder():
    user = User.from_session(db, session)
    if not user:
        return redirect(url_for("login"))
    stats = user.get_stats()
    if request.method == "POST":
        test_path = {
            "desired_sat": request.form.get("desired_sat", ""),
            "desired_act": request.form.get("desired_act", ""),
            "test_date": request.form.get("test_date", ""),
            "test_time": request.form.get("test_time", ""),
            "strengths": request.form.get("strengths", ""),
            "weaknesses": request.form.get("weaknesses", "")
        }
        # First, save the user's updated goals
        stats["test_path"] = test_path
        user.set_stats(stats)

        user_id = user.data[0]
        active_path = db.select(
            "paths", where={"user_id": user_id, "is_active": True})

        # Only generate a new path if one doesn't already exist.
        if not active_path:
            _generate_and_save_new_test_path(
                user_id, test_path['strengths'], test_path['weaknesses'])

        return redirect(url_for("test_path_view"))

    # Pre-fill the form with saved values if they exist
    return render_template("test_path_builder.html", **stats.get("test_path", {}))


@app.route("/dashboard/test-path-view")
@login_required
def test_path_view():
    return render_template("test_path_view.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))


# REPLACE the existing test_path_status function with this one

@app.route('/api/test-path-status')
@login_required
def test_path_status():
    user = User.from_session(db, session)
    if not user:
        return jsonify({"has_path": False, "error": "User not found"}), 404

    # This is more reliable: it checks for an *actual* active path in the database.
    user_id = user.data[0]
    active_tasks = db.select(
        "paths", where={"user_id": user_id, "is_active": True})

    return jsonify({"has_path": bool(active_tasks)})


@app.route('/dashboard/college-path-builder')
@login_required
def college_path_builder():
    return render_template('college_path_builder.html')


# --- API ROUTES FOR THE PATH BUILDER (Fixed) ---

@app.route("/api/tasks", methods=['GET', 'POST'])
@login_required
def api_tasks():
    user = User.from_session(db, session)
    user_id = user.data[0]
    stats = user.get_stats()
    test_path_info = stats.get("test_path", {})
    strengths = test_path_info.get("strengths", "general studying")
    weaknesses = test_path_info.get("weaknesses", "test-taking skills")

    try:
        # Get all active tasks for this user
        active_path = db.select(
            "paths", where={"user_id": user_id, "is_active": True})

        # Generate new path only on POST (explicit regeneration) or if no active path exists
        if request.method == "POST" or not active_path:
            # Deactivate old path before generating new one
            if active_path:
                db.update("paths", {"is_active": False},
                          where={"user_id": user_id})
            tasks = _generate_and_save_new_test_path(
                user_id, strengths, weaknesses)
            return jsonify(tasks)

        # For GET requests with existing active path, return current tasks
        if active_path:
            # Sort by task_order
            active_path = sorted(active_path, key=lambda x: x[2])
            tasks = [{
                "id": row[0],
                "description": row[3],
                "is_completed": bool(row[4]) if row[4] is not None else False
            } for row in active_path]
            return jsonify(tasks)

        # If we get here, there are no active tasks (shouldn't happen normally)
        return jsonify([])

    except Exception as e:
        print(f"API tasks error: {e}")
        return jsonify({"error": "Database error occurred"}), 500

    tasks = []
    for row in active_path:
        tasks.append({
            "id": row[0],
            "description": row[3],
            "is_completed": bool(row[4]) if row[4] is not None else False
        })
    return jsonify(tasks)


@app.route("/api/update_task_status", methods=['POST'])
@login_required
def api_update_task_status():
    user = User.from_session(db, session)
    user_id = user.data[0]
    data = request.get_json()
    status = data.get("status")
    task_id = data.get("taskId")

    if status == 'failed':
        stats = user.get_stats()
        test_path_info = stats.get("test_path", {})
        strengths = test_path_info.get("strengths", "general studying")
        weaknesses = test_path_info.get("weaknesses", "test-taking skills")
        # Regenerate the path if a task is failed
        new_tasks = _generate_and_save_new_test_path(
            user_id, strengths, weaknesses)
        return jsonify({"success": True, "tasks": new_tasks})
    elif status == 'complete' and task_id:
        # Update the specific task's completion status
        db.update("paths", {"is_completed": True}, where={
            "id": task_id, "user_id": user_id})

    return jsonify({"success": True})


@app.route("/api/chat", methods=['POST'])
@login_required
def api_chat():
    user = User.from_session(db, session)
    stats = user.get_stats()
    data = request.get_json()
    history = data.get("history", [])

    # If the history is empty, it's the first message.
    # The frontend will send an empty placeholder user message to trigger the AI's proactive greeting.
    if not history or (len(history) == 1 and history[0]['role'] == 'user' and history[0]['content'] == 'INITIAL_MESSAGE'):
        history = []  # Start with a clean slate for the AI's first turn

    reply = _get_test_prep_ai_chat_response(history, stats)

    # Add the AI's response to the history
    history.append({"role": "assistant", "content": reply})
    # Save the updated history to the session
    session['chat_history'] = history

    return jsonify({"reply": reply})


@app.route("/api/update_stats", methods=['POST'])
@login_required
def api_update_stats():
    user = User.from_session(db, session)
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    data = request.get_json()
    stat_name = data.get("stat_name")  # e.g., "gpa", "sat_math"
    stat_value = data.get("stat_value")

    if not stat_name or stat_value is None:
        return jsonify({"success": False, "error": "Missing stat name or value"}), 400

    try:
        stats = user.get_stats()
        stats[stat_name] = stat_value
        user.set_stats(stats)
        return jsonify({"success": True, "message": "Stats updated successfully"})
    except Exception as e:
        print(f"Error updating stats via API: {e}")
        return jsonify({"success": False, "error": "Server error"}), 500


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
