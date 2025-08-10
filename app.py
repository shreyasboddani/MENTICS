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

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.url_map.strict_slashes = False

db = DatabaseHandler("users.db")

# Setup OpenAI API Key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")


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
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    })


# --- DECORATORS ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# --- AI HELPER FUNCTIONS (Consolidated and Fixed) ---

# REPLACE the existing _get_ai_tasks function with this one
def _get_ai_tasks(strengths, weaknesses, user_stats={}):
    """Generates tasks from AI, with a reliable 5-task mock fallback."""

    # This is the single source of mock tasks, ensuring consistency.
    def get_mock_tasks_reliably():
        print("Warning: OPENAI_API_KEY not set or AI failed. Returning mock tasks.")
        all_mock_tasks = [
            {"description":
                "Focus on circle theorems and properties of triangles (Mock)."},
            {"description":
                "Complete a drill on comma, semicolon, and colon usage (Mock)."},
            {"description":
                "Solidify your algebra skills with advanced function problems (Mock)."},
            {"description":
                "Complete a timed mini-section for your weakest subject (Mock)."},
            {"description":
                "Review 20 new vocabulary words using flashcards (Mock)."},
            {"description":
                "Analyze the structure of a sample essay prompt (Mock)."},
            {"description":
                "Practice reading comprehension with a news article (Mock)."},
            {"description":
                "Take a 15-minute quiz on data interpretation graphs (Mock)."}
        ]
        return random.sample(all_mock_tasks, 5)

    if not openai.api_key:
        return get_mock_tasks_reliably()

    # --- ENHANCED PROMPT ---
    # Get more context from the user's stats
    desired_sat = user_stats.get("test_path", {}).get("desired_sat", "N/A")
    desired_act = user_stats.get("test_path", {}).get("desired_act", "N/A")
    current_gpa = user_stats.get("gpa", "N/A")

    prompt = (
        f"A student has the following profile:\n"
        f"- Strengths: '{strengths}'\n"
        f"- Weaknesses: '{weaknesses}'\n"
        f"- Current GPA: {current_gpa}\n"
        f"- Desired SAT Score: {desired_sat}\n"
        f"- Desired ACT Score: {desired_act}\n\n"
        "Based on this, create a 5-step study plan. "
        "Return ONLY a valid JSON object with a key 'tasks', which is an array of 5 objects, "
        "each with a 'description' key."
    )
    # --- END OF ENHANCED PROMPT ---

    try:
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a test prep tutor who provides study plans in JSON format."},
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
        print(f"AI task generation failed: {e}")
        return get_mock_tasks_reliably()


def _get_ai_chat_response(history, user_stats):
    """Gets a chat response from the AI, with a mock fallback."""
    if not openai.api_key:
        return "I'm currently in offline mode and can't chat right now."

    system_message = {
        "role": "system",
        "content": f"You are a helpful test prep assistant. Student's profile: {json.dumps(user_stats)}. Keep answers concise."
    }
    messages = [system_message] + history

    try:
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo", messages=messages)
        return completion.choices[0].message.content
    except Exception as e:
        print(f"AI chat response failed: {e}")
        return "Sorry, I encountered an error connecting to the AI."


# REPLACE the existing _generate_and_save_new_path function with this one
def _generate_and_save_new_path(user_id, strengths, weaknesses):
    """Deactivates old path, gets new tasks, and saves them."""
    # Fetch the user's full data record from the database using their ID
    user_record = db.select("users", where={"id": user_id})
    user_stats = {}  # Default to empty stats
    if user_record:
        # The stats are in the 4th column (index 3), stored as a JSON string
        user_stats = json.loads(user_record[0][3])

    # Deactivate the old path
    db.update("paths", {"is_active": False}, where={"user_id": user_id})

    # Pass the full context to the AI task generator
    tasks = _get_ai_tasks(strengths, weaknesses, user_stats)

    saved_tasks = []
    for i, task in enumerate(tasks):
        task_id = db.insert("paths", {
            "user_id": user_id,
            "task_order": i + 1,
            "description": task.get("description", "No description provided."),
            "is_active": True,
            "is_completed": False
        })
        saved_tasks.append({
            "id": task_id,
            "description": task.get("description", "No description provided."),
            "is_completed": False
        })
    return saved_tasks


# --- ORIGINAL PAGE ROUTES (Unchanged) ---
@app.route("/")
def home():
    return render_template("index.html")

# Signup route


@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        try:
            db.insert("users", {
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
            return redirect(url_for("login"))
        except Exception as e:
            print(f"Signup error: {e}")
            error = "Email already exists!"
    return render_template("signup.html", error=error)

# Login route


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = db.select("users", where={"email": email})
        if user and check_password_hash(user[0][2], password):
            session["user"] = user[0][1]
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
    test_prep_upcoming = stats.get("test_prep_upcoming", 0)
    college_planning_upcoming = stats.get("college_planning_upcoming", 0)
    return render_template(
        "dashboard.html",
        test_prep_upcoming=test_prep_upcoming,
        college_planning_upcoming=college_planning_upcoming,
        gpa=stats.get("gpa", "")
    )


@app.route("/dashboard/stats", methods=["GET"])
@login_required
def stats():
    user = User.from_session(db, session)
    if not user:
        return redirect(url_for("login"))
    stats = user.get_stats()
    # Default values if not set yet
    test_prep_completed = stats.get("test_prep_completed", 0)
    test_prep_upcoming = stats.get("test_prep_upcoming", 0)
    college_planning_completed = stats.get("college_planning_completed", 0)
    college_planning_upcoming = stats.get("college_planning_upcoming", 0)
    return render_template(
        "stats.html",
        test_prep_completed=test_prep_completed,
        test_prep_upcoming=test_prep_upcoming,
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
        stats["test_path"] = test_path
        user.set_stats(stats)
        # Generate the first path upon submission
        _generate_and_save_new_path(
            user.data[0], test_path['strengths'], test_path['weaknesses'])
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


@app.route('/api/test-path-status')
@login_required
def test_path_status():
    """
    FIXED: This function now correctly checks for an existing active path
    and returns the JSON key 'has_path' (snake_case) that the frontend expects.
    """
    user = User.from_session(db, session)
    if not user:
        # This case is handled by @login_required, but as a fallback:
        return jsonify({"has_path": False, "error": "User not found"}), 404

    # A user has a "path" if they have active tasks in the 'paths' table.
    # This is more reliable than checking if the form fields in 'stats' are empty.
    user_id = user.data[0]
    active_tasks = db.select(
        "paths", where={"user_id": user_id, "is_active": True})

    # Return a boolean indicating if any active tasks were found.
    # The key 'has_path' now matches the frontend JavaScript.
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
        active_path = db.select("paths", where={
            "user_id": user_id, "is_active": True})

        # Sort the tasks by task_order if active_path exists
        if active_path:
            # Sort by task_order column
            active_path = sorted(active_path, key=lambda x: x[2])

        # Generate a new path if one doesn't exist or if a regeneration is forced via POST
        if request.method == "POST" or not active_path:
            tasks = _generate_and_save_new_path(user_id, strengths, weaknesses)
            return jsonify(tasks)
    except Exception as e:  # It's better to catch specific database errors
        print(f"API tasks error: {e}")
        return jsonify({"error": "Could not retrieve or generate tasks due to a server error."}), 500

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
        new_tasks = _generate_and_save_new_path(user_id, strengths, weaknesses)
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

    reply = _get_ai_chat_response(history, stats)
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
