from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dbhelper import DatabaseHandler
from userhelper import User
from functools import wraps
import json
import google.generativeai as genai
import os
from dotenv import load_dotenv
import random
from pathlib import Path
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

# Configure the Gemini API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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
        "category": "TEXT"
    })
    db.create_table("stat_history", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id": "INTEGER NOT NULL",
        "stat_name": "TEXT NOT NULL",
        "stat_value": "TEXT NOT NULL",
        "recorded_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    })
    # NEW: Table to store chat history
    db.create_table("chat_conversations", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id": "INTEGER NOT NULL",
        "category": "TEXT NOT NULL",
        "history": "TEXT NOT NULL",
        "UNIQUE": "(user_id, category)"
    })

# --- DECORATORS ---


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# --- AI HELPER FUNCTIONS (No changes needed in these) ---


def _get_test_prep_ai_tasks(strengths, weaknesses, user_stats={}, chat_history=[], path_history={}):
    """Generates test preparation tasks with a hyper-detailed prompt for maximum reliability."""

    def get_mock_tasks_reliably():
        print("--- DEBUG: Running corrected Test Prep mock generator. ---")
        # This mock function is now more realistic to the new rules
        all_mock_tasks = [
            {"description": "Take a full-length, timed SAT practice test.",
                "type": "milestone", "stat_to_update": "sat_total", "category": "Test Prep"},
            {"description": "Review algebra concepts from your SAT practice test.",
                "type": "standard", "stat_to_update": None, "category": "Test Prep"},
            {"description": "Practice 15 difficult vocabulary words.", "type": "standard",
                "stat_to_update": None, "category": "Test Prep"},
            {"description": "Take a timed ACT Science practice section.", "type": "milestone",
                "stat_to_update": "act_science", "category": "Test Prep"}
        ]
        return random.sample(all_mock_tasks, 4) + [{"description": "Work on time management strategies for the reading section.", "type": "standard", "stat_to_update": None, "category": "Test Prep"}]

    if not os.getenv("GEMINI_API_KEY"):
        return get_mock_tasks_reliably()

    completed_tasks_str = "\n".join(
        [f"- {task[3]}" for task in path_history.get('completed', [])]) or "None."
    incomplete_tasks_str = "\n".join(
        [f"- {task[3]}" for task in path_history.get('incomplete', [])]) or "None."
    chat_history_str = "\n".join(
        [f"{msg['role'].capitalize()}: {msg['content']}" for msg in chat_history]) or "No conversation history yet."

    days_left = "Not set"
    test_date_str = user_stats.get("test_path", {}).get("test_date")
    if test_date_str:
        try:
            delta = datetime.strptime(
                test_date_str, '%Y-%m-%d') - datetime.now()
            days_left = f"{delta.days} days remaining"
        except ValueError:
            days_left = "Invalid date format"

    prompt = (
        f"# CONTEXT\n"
        f"You are an expert AI test prep (SAT & ACT) coach creating a study plan for a high school student.\n"
        f"The student's test is in: {days_left}.\n\n"
        f"# STUDENT PROFILE\n"
        f"- Strengths: {strengths}\n"
        f"- Weaknesses: {weaknesses}\n\n"
        f"# STUDENT HISTORY\n"
        f"## Recently Completed Tasks:\n{completed_tasks_str}\n\n"
        f"## Recently Incomplete or Failed Tasks:\n{incomplete_tasks_str}\n\n"
        f"## Recent Conversation:\n{chat_history_str}\n\n"
        f"# YOUR TASK\n"
        f"Generate a new, 5-step study plan based on all the context provided. You MUST adapt the plan based on the student's recent conversation. The new plan must logically progress from previous tasks and chat history.\n\n"
        f"# CRITICAL RULES\n"
        f"- Your ENTIRE output must be a single, raw JSON object.\n"
        f"- **Focus is Key:** If the user's conversation indicates a preference for ONLY the SAT or ONLY the ACT, you MUST generate tasks for that specific test. Do not include tasks for the other test.\n"
        f"- **Stat Updates for Milestones Only:** The 'stat_to_update' field should ONLY be used for 'milestone' tasks that involve completing a practice test. Standard review tasks should have 'stat_to_update' set to null.\n"
        f"- **Specific Stat Names:** When a milestone is a practice test, the 'stat_to_update' value must match the specific test section (e.g., 'sat_math', 'act_science'). For a full SAT test, use 'sat_total'.\n"
        f"- The plan must contain exactly 5 task objects and must be novel.\n\n"
        f"# JSON SCHEMA\n"
        f"Your output must conform to this exact structure:\n"
        f"{{\n"
        f'  "tasks": [\n'
        f'    {{\n'
        f'      "description": "A string describing the specific, actionable task.",\n'
        f'      "type": "A string, either \'standard\' or \'milestone\'.",\n'
        f'      "stat_to_update": "A string ONLY if type is milestone (must be one of [\'sat_math\', \'sat_ebrw\', \'sat_total\', \'act_math\', \'act_reading\', \'act_science\']), otherwise null.",\n'
        f'      "category": "This MUST be the string \'Test Prep\'."\n'
        f'    }}\n'
        f'  ]\n'
        f'}}'
    )

    try:
        model = genai.GenerativeModel(
            'gemini-2.5-flash-lite',
            generation_config={"response_mime_type": "application/json"}
        )
        response = model.generate_content(prompt)
        response_data = json.loads(response.text)
        tasks = response_data.get("tasks", [])
        if isinstance(tasks, list) and len(tasks) == 5:
            return tasks
        raise ValueError("Invalid format from AI")
    except Exception as e:
        print(f"\n--- GEMINI API ERROR IN _get_test_prep_ai_tasks: {e} ---\n")
        return get_mock_tasks_reliably()


def _get_test_prep_ai_chat_response(history, user_stats):
    if not os.getenv("GEMINI_API_KEY"):
        return "I'm in testing mode, but I'm saving our conversation!"

    days_left = "a future date"
    test_date_str = user_stats.get("test_path", {}).get("test_date")
    if test_date_str:
        try:
            test_date = datetime.strptime(test_date_str, '%Y-%m-%d')
            delta = test_date - datetime.now()
            days_left = f"{delta.days} days"
        except ValueError:
            pass

    system_message = (
        "You are a friendly and proactive study coach. Your student's test is in "
        f"{days_left}. If the conversation history is empty, greet the user, "
        "remind them of their test date, and ask what they'd like to focus on. "
        "Also, let them know they can say 'regenerate' or 'new path' to get an updated plan based on our chat. "
        "In subsequent messages, be an encouraging tutor. Acknowledge scores and struggles. "
        "If the user asks to change focus or regenerate their path, confirm that you will create a new path for them."
    )

    gemini_history = []
    for message in history:
        role = "model" if message["role"] == "assistant" else "user"
        gemini_history.append({"role": role, "parts": [message["content"]]})

    try:
        model = genai.GenerativeModel(
            'gemini-2.5-flash-lite', system_instruction=system_message)
        chat = model.start_chat(history=gemini_history[:-1])
        last_user_message = gemini_history[-1]['parts'][0] if gemini_history else "Hello"
        response = chat.send_message(last_user_message)
        return response.text
    except Exception as e:
        print(
            f"\n--- GEMINI API ERROR IN _get_test_prep_ai_chat_response: {e} ---\n")
        return "Sorry, I encountered an error connecting to the AI."


def _generate_and_save_new_test_path(user_id, strengths, weaknesses, chat_history=[]):
    user_record = db.select("users", where={"id": user_id})
    user_stats = json.loads(user_record[0][3]) if user_record else {}

    all_tasks = db.select(
        "paths", where={"user_id": user_id, "category": "Test Prep"})
    path_history = {
        "completed": [task for task in all_tasks if task[4]],
        "incomplete": [task for task in all_tasks if not task[4]]
    }

    db.update("paths", {"is_active": False}, where={
              "user_id": user_id, "category": "Test Prep"})

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
            "category": "Test Prep",
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


def _get_college_planning_ai_tasks(college_context, user_stats, path_history, chat_history=[]):
    """Generates college planning tasks with a hyper-detailed prompt."""

    def get_mock_tasks_reliably():
        print("--- DEBUG: Running corrected College Planning mock generator. ---")
        all_mock_tasks = [
            {"description": "Research 5 colleges that match your interests.", "type": "standard",
                "stat_to_update": None, "category": "College Planning"},
            {"description": "Write a rough draft of your Common App personal statement.",
                "type": "milestone", "stat_to_update": "essay_progress", "category": "College Planning"},
            {"description": "Update your GPA in your profile.", "type": "milestone",
                "stat_to_update": "gpa", "category": "College Planning"},
            {"description": "Request three letters of recommendation from teachers.",
                "type": "standard", "stat_to_update": None, "category": "College Planning"},
            {"description": "Create a spreadsheet to track application deadlines.",
                "type": "standard", "stat_to_update": None, "category": "College Planning"}
        ]
        return random.sample(all_mock_tasks, 5)

    if not os.getenv("GEMINI_API_KEY"):
        return get_mock_tasks_reliably()

    completed_tasks_str = "\n".join(
        [f"- {task[3]}" for task in path_history.get('completed', [])]) or "None."
    incomplete_tasks_str = "\n".join(
        [f"- {task[3]}" for task in path_history.get('incomplete', [])]) or "None."
    chat_history_str = "\n".join(
        [f"{msg['role'].capitalize()}: {msg['content']}" for msg in chat_history]) or "No conversation history yet."

    prompt = (
        f"# CONTEXT\n"
        f"You are an expert AI college admissions counselor creating a personalized roadmap for a high school student.\n\n"
        f"# STUDENT PROFILE\n"
        f"- Current Grade: {college_context.get('grade', 'N/A')}\n"
        f"- Current Planning Stage: {college_context.get('planning_stage', 'N/A')}\n"
        f"- Interested Majors: {college_context.get('majors', 'N/A')}\n"
        f"- Target Colleges: {college_context.get('target_colleges', 'None specified')}\n"
        f"- Current GPA: {user_stats.get('gpa', 'N/A')}\n\n"
        f"# STUDENT HISTORY\n"
        f"## Recently Completed Tasks:\n{completed_tasks_str}\n\n"
        f"## Recently Incomplete or Failed Tasks:\n{incomplete_tasks_str}\n\n"
        f"## Recent Conversation:\n{chat_history_str}\n\n"
        f"# YOUR TASK\n"
        f"Generate a new, 5-step college planning roadmap based on all the context provided. You MUST adapt the plan based on the student's recent conversation and planning stage. The new plan must logically progress from previous tasks and chat history.\n\n"
        f"# CRITICAL RULES\n"
        f"- Your ENTIRE output must be a single, raw JSON object.\n"
        f"- **Stat Updates for Milestones Only:** The 'stat_to_update' field should ONLY be used for 'milestone' tasks that represent major goals (like 'essay_progress', 'applications_submitted', or 'gpa'). Standard research or small tasks should have 'stat_to_update' set to null.\n"
        f"- The plan must contain exactly 5 task objects and must be novel.\n\n"
        f"# JSON SCHEMA\n"
        f"Your output must conform to this exact structure:\n"
        f"{{\n"
        f'  "tasks": [\n'
        f'    {{\n'
        f'      "description": "A string describing the specific, actionable task.",\n'
        f'      "type": "A string, either \'standard\' or \'milestone\'.",\n'
        f'      "stat_to_update": "A string ONLY if type is milestone (e.g., \'essay_progress\', \'applications_submitted\', \'gpa\'), otherwise null.",\n'
        f'      "category": "This MUST be the string \'College Planning\'."\n'
        f'    }}\n'
        f'  ]\n'
        f'}}'
    )

    try:
        model = genai.GenerativeModel(
            'gemini-2.5-flash-lite',
            generation_config={"response_mime_type": "application/json"}
        )
        response = model.generate_content(prompt)
        response_data = json.loads(response.text)
        tasks = response_data.get("tasks", [])
        if isinstance(tasks, list) and len(tasks) == 5:
            return tasks
        raise ValueError("Invalid format from AI")
    except Exception as e:
        print(
            f"\n--- GEMINI API ERROR IN _get_college_planning_ai_tasks: {e} ---\n")
        return get_mock_tasks_reliably()


def _get_college_planning_ai_chat_response(history, user_stats):
    """Generates a proactive and context-aware chat response for college planning."""
    if not os.getenv("GEMINI_API_KEY"):
        return "I'm in testing mode, but I'm saving our conversation!"

    college_info = user_stats.get("college_path", {})
    system_message = (
        "You are a friendly and proactive college planning advisor. The student is in "
        f"grade {college_info.get('grade', 'N/A')} and is in the '{college_info.get('planning_stage', 'N/A')}' stage. "
        "If the conversation is just beginning, greet the user and ask what specific part of college planning they want to discuss (e.g., essays, applications, college lists). "
        "Also, let them know they can say 'regenerate' or 'new path' to get an updated plan based on our chat. "
        "In subsequent messages, be an encouraging and helpful advisor. If the user asks to change their path, confirm you will regenerate it for them."
    )
    gemini_history = []
    for message in history:
        role = "model" if message["role"] == "assistant" else "user"
        gemini_history.append({"role": role, "parts": [message["content"]]})

    try:
        model = genai.GenerativeModel(
            'gemini-2.5-flash-lite', system_instruction=system_message)
        chat = model.start_chat(history=gemini_history[:-1])
        last_user_message = gemini_history[-1]['parts'][0] if gemini_history else "Hello"
        response = chat.send_message(last_user_message)
        return response.text
    except Exception as e:
        print(
            f"\n--- GEMINI API ERROR IN _get_college_planning_ai_chat_response: {e} ---\n")
        return "Sorry, I encountered an error connecting to the AI."


def _generate_and_save_new_college_path(user_id, college_context, chat_history=[]):
    """Gathers all context, generates, and saves a new college planning path."""
    try:
        user_record = db.select("users", where={"id": user_id})
        if not user_record:
            raise ValueError(f"User with ID {user_id} not found.")
        user_stats = json.loads(user_record[0][3])

        all_college_tasks = db.select(
            "paths", where={"user_id": user_id, "category": "College Planning"})
        path_history = {
            "completed": [task for task in all_college_tasks if task[4]],
            "incomplete": [task for task in all_college_tasks if not task[4]]
        }

        db.update("paths", {"is_active": False}, where={
                  "user_id": user_id, "category": "College Planning"})

        tasks = _get_college_planning_ai_tasks(
            college_context, user_stats, path_history, chat_history)

        if not tasks or len(tasks) != 5:
            raise ValueError(
                "AI task generation did not return the expected 5 tasks.")

        saved_tasks = []
        for i, task_data in enumerate(tasks):
            task_id = db.insert("paths", {
                "user_id": user_id,
                "task_order": i + 1,
                "description": task_data.get("description"),
                "type": task_data.get("type"),
                "stat_to_update": task_data.get("stat_to_update"),
                "category": "College Planning",
                "is_active": True,
                "is_completed": False
            })
            saved_tasks.append(
                {**task_data, "id": task_id, "is_completed": False})

        return saved_tasks
    except Exception as e:
        print(f"Error in _generate_and_save_new_college_path: {e}")
        return []

# --- Standard Routes (No changes needed) ---


@app.route("/dashboard/college-path-builder", methods=["GET", "POST"])
@login_required
def college_path_builder():
    user = User.from_session(db, session)
    if not user:
        return redirect(url_for('login'))

    stats = user.get_stats()
    college_stats = stats.get('college_path', {})

    if request.method == "POST":
        college_context = {
            'grade': request.form.get('current_grade'),
            'planning_stage': request.form.get('planning_stage'),
            'majors': request.form.get('interested_majors'),
            'target_colleges': request.form.get('target_colleges', '')
        }
        stats['college_path'] = college_context
        user.set_stats(stats)
        _generate_and_save_new_college_path(user.data[0], college_context)
        return redirect(url_for('college_path_view'))

    return render_template(
        "college_path_builder.html",
        **college_stats
    )


@app.route('/dashboard/college-path-view')
@login_required
def college_path_view():
    return render_template("college_path_view.html")


@app.route("/")
def home():
    is_logged_in = "user" in session
    return render_template("index.html", is_logged_in=is_logged_in)


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
                    "sat_ebrw": "", "sat_math": "", "act_math": "",
                    "act_reading": "", "act_science": "", "gpa": "", "milestones": 0
                })
            })
            session["user"] = email
            session["user_id"] = user_id
            session.permanent = True
            return redirect(url_for("dashboard"))
        except Exception as e:
            print(f"Signup error: {e}")
            error = "Email already exists!"
    return render_template("signup.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if "user" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user_record = db.select("users", where={"email": email})
        if user_record and check_password_hash(user_record[0][2], password):
            session["user"] = user_record[0][1]
            session["user_id"] = user_record[0][0]
            session.permanent = True
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid credentials"
    return render_template("login.html", error=error)


@app.route("/dashboard")
@login_required
def dashboard():
    user = User.from_session(db, session)
    if not user:
        return redirect(url_for("login"))
    stats = user.get_stats()
    user_id = user.data[0]
    all_tasks = db.select("paths", where={"user_id": user_id})

    active_test_tasks = [t for t in all_tasks if t[5] and t[9] == 'Test Prep']
    test_prep_completed_current = sum(1 for t in active_test_tasks if t[4])
    total_test_prep_completed = sum(
        1 for t in all_tasks if t[4] and t[9] == 'Test Prep')

    active_college_tasks = [
        t for t in all_tasks if t[5] and t[9] == 'College Planning']
    college_planning_completed_current = sum(
        1 for t in active_college_tasks if t[4])
    total_college_planning_completed = sum(
        1 for t in all_tasks if t[4] and t[9] == 'College Planning')

    return render_template(
        "dashboard.html",
        test_prep_completed=test_prep_completed_current,
        total_test_prep_completed=total_test_prep_completed,
        college_planning_completed=college_planning_completed_current,
        total_college_planning_completed=total_college_planning_completed,
        gpa=stats.get("gpa", "")
    )


@app.route("/dashboard/stats", methods=["GET"])
@login_required
def stats():
    user = User.from_session(db, session)
    if not user:
        return redirect(url_for("login"))
    stats = user.get_stats()

    all_tasks = db.select("paths", where={"user_id": user.data[0]})

    active_test_tasks = [t for t in all_tasks if t[5] and t[9] == 'Test Prep']
    test_prep_completed = sum(1 for t in active_test_tasks if t[4])
    total_test_prep_completed = sum(
        1 for t in all_tasks if t[4] and t[9] == 'Test Prep')

    active_college_tasks = [
        t for t in all_tasks if t[5] and t[9] == 'College Planning']
    college_planning_completed_current = sum(
        1 for t in active_college_tasks if t[4])
    total_college_planning_completed = sum(
        1 for t in all_tasks if t[4] and t[9] == 'College Planning')

    return render_template(
        "stats.html",
        test_prep_completed=test_prep_completed,
        total_test_prep_completed=total_test_prep_completed,
        college_planning_completed_current=college_planning_completed_current,
        total_college_planning_completed=total_college_planning_completed,
        gpa=stats.get("gpa", ""), sat_ebrw=stats.get("sat_ebrw", ""),
        sat_math=stats.get("sat_math", ""), act_math=stats.get("act_math", ""),
        act_reading=stats.get("act_reading", ""), act_science=stats.get("act_science", "")
    )


@app.route("/dashboard/stats/edit", methods=["GET", "POST"])
@login_required
def edit_stats():
    user = User.from_session(db, session)
    if not user:
        return redirect(url_for("login"))
    stats = user.get_stats()
    if request.method == "POST":
        stats["sat_ebrw"] = request.form.get("sat_ebrw", "")
        stats["sat_math"] = request.form.get("sat_math", "")
        stats["act_math"] = request.form.get("act_math", "")
        stats["act_reading"] = request.form.get("act_reading", "")
        stats["act_science"] = request.form.get("act_science", "")
        stats["gpa"] = request.form.get("gpa", "")
        user.set_stats(stats)
        return redirect(url_for("stats"))

    return render_template(
        "edit_stats.html",
        sat_ebrw=stats.get("sat_ebrw", ""),
        sat_math=stats.get("sat_math", ""),
        act_math=stats.get("act_math", ""),
        act_reading=stats.get("act_reading", ""),
        act_science=stats.get("act_science", ""),
        gpa=stats.get("gpa", "")
    )


@app.route("/dashboard/tracker")
@login_required
def tracker():
    user = User.from_session(db, session)
    if not user:
        return redirect(url_for("login"))

    user_id = user.data[0]
    all_tasks = db.select(
        "paths", where={"user_id": user_id}, order_by="created_at DESC")
    stats = user.get_stats()

    history_records = db.select(
        "stat_history", where={"user_id": user_id}, order_by="recorded_at ASC")

    sat_history = []
    act_history = []
    temp_sat_scores = {}

    for record in history_records:
        stat_name, stat_value, recorded_at = record[2], record[3], record[4]
        if "sat" in stat_name:
            date_key = recorded_at.split(" ")[0]
            if date_key not in temp_sat_scores:
                temp_sat_scores[date_key] = {}
            temp_sat_scores[date_key][stat_name] = int(stat_value)
        elif "act" in stat_name:
            act_history.append({"date": recorded_at, "score": int(stat_value)})

    for date, scores in temp_sat_scores.items():
        if "sat_math" in scores and "sat_ebrw" in scores:
            sat_history.append(
                {"date": date, "score": scores["sat_math"] + scores["sat_ebrw"]})

    stats['sat_history'] = sat_history
    stats['act_history'] = act_history

    test_prep_generations, college_planning_generations = {}, {}
    for task in all_tasks:
        generation_key, category = task[6], task[9]
        if category == 'Test Prep':
            if generation_key not in test_prep_generations:
                test_prep_generations[generation_key] = []
            test_prep_generations[generation_key].append(task)
        elif category == 'College Planning':
            if generation_key not in college_planning_generations:
                college_planning_generations[generation_key] = []
            college_planning_generations[generation_key].append(task)

    return render_template(
        "tracker.html",
        stats=stats,
        test_prep_generations=test_prep_generations,
        college_planning_generations=college_planning_generations
    )


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
        user_id = user.data[0]
        _generate_and_save_new_test_path(
            user_id, test_path['strengths'], test_path['weaknesses'])
        return redirect(url_for("test_path_view"))
    return render_template("test_path_builder.html", **stats.get("test_path", {}))


@app.route("/dashboard/test-path-view")
@login_required
def test_path_view():
    return render_template("test_path_view.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

# --- API ROUTES ---


@app.route('/api/test-path-status')
@login_required
def test_path_status():
    user = User.from_session(db, session)
    if not user:
        return jsonify({"has_path": False, "error": "User not found"}), 404
    user_id = user.data[0]
    active_tasks = db.select(
        "paths", where={"user_id": user_id, "is_active": True, "category": "Test Prep"})
    return jsonify({"has_path": bool(active_tasks)})


@app.route('/api/college-path-status')
@login_required
def college_path_status():
    user = User.from_session(db, session)
    if not user:
        return jsonify({"has_path": False, "error": "User not found"}), 404
    user_id = user.data[0]
    active_tasks = db.select(
        "paths", where={"user_id": user_id, "is_active": True, "category": "College Planning"})
    return jsonify({"has_path": bool(active_tasks)})


@app.route("/api/tasks", methods=['GET', 'POST'])
@login_required
def api_tasks():
    user = User.from_session(db, session)
    user_id = user.data[0]
    stats = user.get_stats()
    category = request.args.get('category', 'Test Prep')
    try:
        active_path = db.select(
            "paths", where={"user_id": user_id, "is_active": True, "category": category})
        if request.method == "POST" or not active_path:
            chat_record = db.select("chat_conversations", where={
                                    "user_id": user_id, "category": category})
            chat_history = json.loads(chat_record[0][3]) if chat_record else []
            if category == 'College Planning':
                college_context = stats.get("college_path", {})
                tasks = _generate_and_save_new_college_path(
                    user_id, college_context, chat_history)
            else:
                test_path_info = stats.get("test_path", {})
                strengths = test_path_info.get("strengths", "general studying")
                weaknesses = test_path_info.get(
                    "weaknesses", "test-taking skills")
                tasks = _generate_and_save_new_test_path(
                    user_id, strengths, weaknesses, chat_history)
            return jsonify(tasks)

        if active_path:
            active_path = sorted(active_path, key=lambda x: x[2])
            tasks = [{"id": r[0], "description": r[3], "is_completed": bool(r[4]),
                      "type": r[7], "stat_to_update": r[8]} for r in active_path]
            return jsonify(tasks)
        return jsonify([])
    except Exception as e:
        print(f"API tasks error for category {category}: {e}")
        return jsonify({"error": "An error occurred"}), 500


@app.route("/api/update_task_status", methods=['POST'])
@login_required
def api_update_task_status():
    user = User.from_session(db, session)
    user_id = user.data[0]
    data = request.get_json()
    status = data.get("status")
    task_id = data.get("taskId")

    if status == 'failed':
        task_info = db.select(
            "paths", where={"id": task_id, "user_id": user_id})
        if not task_info:
            return jsonify({"success": False, "error": "Task not found"}), 404
        category = task_info[0][9]
        stats = user.get_stats()
        chat_record = db.select("chat_conversations", where={
                                "user_id": user_id, "category": category})
        chat_history = json.loads(chat_record[0][3]) if chat_record else []

        if category == 'College Planning':
            college_context = stats.get("college_path", {})
            new_tasks = _generate_and_save_new_college_path(
                user_id, college_context, chat_history)
        else:
            test_path_info = stats.get("test_path", {})
            strengths = test_path_info.get("strengths", "general studying")
            weaknesses = test_path_info.get("weaknesses", "test-taking skills")
            new_tasks = _generate_and_save_new_test_path(
                user_id, strengths, weaknesses, chat_history)
        return jsonify({"success": True, "tasks": new_tasks})
    elif status == 'complete' and task_id:
        db.update("paths", {"is_completed": True}, where={
                  "id": task_id, "user_id": user_id})
    return jsonify({"success": True})


# MODIFIED: Now saves chat history to the database
@app.route("/api/chat", methods=['POST'])
@login_required
def api_chat():
    user = User.from_session(db, session)
    user_id = user.data[0]
    stats = user.get_stats()
    data = request.get_json()
    history = data.get("history", [])
    category = request.args.get('category', 'Test Prep')

    if not history or (len(history) == 1 and history[0]['role'] == 'user' and history[0]['content'] == 'INITIAL_MESSAGE'):
        history = []

    user_message = history[-1]['content'].lower() if history else ""
    if "regenerate" in user_message or "new path" in user_message or "change" in user_message:
        if category == 'College Planning':
            college_context = stats.get("college_path", {})
            new_tasks = _generate_and_save_new_college_path(
                user_id, college_context, chat_history=history)
        else:
            test_path_info = stats.get("test_path", {})
            strengths = test_path_info.get("strengths", "general studying")
            weaknesses = test_path_info.get("weaknesses", "test-taking skills")
            new_tasks = _generate_and_save_new_test_path(
                user_id, strengths, weaknesses, chat_history=history)

        # Save chat history after regeneration
        if history:
            history.append(
                {"role": "assistant", "content": "I've generated a new path for you based on our conversation."})
            history_json = json.dumps(history)
            existing_chat = db.select("chat_conversations", where={
                                      "user_id": user_id, "category": category})
            if existing_chat:
                db.update("chat_conversations", {"history": history_json}, where={
                          "user_id": user_id, "category": category})
            else:
                db.insert("chat_conversations", {
                          "user_id": user_id, "category": category, "history": history_json})

        return jsonify({"new_path": new_tasks})

    if category == 'College Planning':
        reply = _get_college_planning_ai_chat_response(history, stats)
    else:
        reply = _get_test_prep_ai_chat_response(history, stats)

    history.append({"role": "assistant", "content": reply})

    # Save to DB
    history_json = json.dumps(history)
    existing_chat = db.select("chat_conversations", where={
                              "user_id": user_id, "category": category})
    if existing_chat:
        db.update("chat_conversations", {"history": history_json}, where={
                  "user_id": user_id, "category": category})
    else:
        db.insert("chat_conversations", {
                  "user_id": user_id, "category": category, "history": history_json})

    return jsonify({"reply": reply})

# NEW: Endpoint to get chat history


@app.route('/api/chat_history')
@login_required
def get_chat_history():
    user = User.from_session(db, session)
    user_id = user.data[0]
    category = request.args.get('category')
    chat_record = db.select("chat_conversations", where={
                            "user_id": user_id, "category": category})
    if chat_record:
        history = json.loads(chat_record[0][3])
        return jsonify(history)
    return jsonify([])

# NEW: Endpoint to reset chat history


@app.route('/api/reset_chat', methods=['POST'])
@login_required
def reset_chat_history():
    user = User.from_session(db, session)
    user_id = user.data[0]
    data = request.get_json()
    category = data.get('category')
    if not category:
        return jsonify({"success": False, "error": "Category is required"}), 400
    try:
        db.delete("chat_conversations", where={
                  "user_id": user_id, "category": category})
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error resetting chat: {e}")
        return jsonify({"success": False, "error": "Could not reset chat"}), 500


@app.route("/api/update_stats", methods=['POST'])
@login_required
def api_update_stats():
    user = User.from_session(db, session)
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
    data = request.get_json()
    stat_name = data.get("stat_name")
    stat_value = data.get("stat_value")

    if not stat_name or stat_value is None:
        return jsonify({"success": False, "error": "Missing stat name or value"}), 400
    try:
        stats = user.get_stats()
        stats[stat_name] = stat_value
        user.set_stats(stats)
        db.insert("stat_history", {
            "user_id": user.data[0],
            "stat_name": stat_name,
            "stat_value": stat_value
        })
        return jsonify({"success": True, "message": "Stats updated successfully"})
    except Exception as e:
        print(f"Error updating stats via API: {e}")
        return jsonify({"success": False, "error": "Server error"}), 500


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
# --- END OF FILE ---
