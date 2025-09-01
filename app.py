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


# In app.py, REPLACE your init_db function
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
        "category": "TEXT"  # <-- This column is now added
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
        print("--- DEBUG: Running corrected Test Prep mock generator. ---")
        all_mock_tasks = [
            {"description": "Focus on circle theorems.", "type": "standard",
                "stat_to_update": None, "category": "Test Prep"},
            {"description": "Complete a timed SAT Math section and record your score in the chat.",
                "type": "milestone", "stat_to_update": "sat_math", "category": "Test Prep"},
            {"description": "Review 20 new vocabulary words using flashcards.",
                "type": "standard", "stat_to_update": None, "category": "Test Prep"},
            {"description": "Practice reading comprehension passages.",
                "type": "standard", "stat_to_update": None, "category": "Test Prep"},
            {"description": "Take a full ACT Science practice test.", "type": "milestone",
                "stat_to_update": "act_science", "category": "Test Prep"}
        ]
        return random.sample(all_mock_tasks, 5)

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

# In app.py, ADD this new function in the AI HELPER FUNCTIONS section


def _get_college_planning_ai_tasks(college_context, user_stats, path_history):
    """Generates college planning tasks with a hyper-detailed prompt."""

    def get_mock_tasks_reliably():
        print("--- DEBUG: Running corrected College Planning mock generator. ---")
        all_mock_tasks = [
            {"description": "Research 5 colleges that match your interests.", "type": "milestone",
                "stat_to_update": "colleges_researched", "category": "College Planning"},
            {"description": "Write a rough draft of your Common App personal statement.",
                "type": "milestone", "stat_to_update": "essay_progress", "category": "College Planning"},
            {"description": "Complete the activities section of the Common App.",
                "type": "standard", "stat_to_update": None, "category": "College Planning"},
            {"description": "Request three letters of recommendation from teachers.",
                "type": "standard", "stat_to_update": None, "category": "College Planning"},
            {"description": "Create a spreadsheet to track application deadlines.",
                "type": "standard", "stat_to_update": None, "category": "College Planning"}
        ]
        return random.sample(all_mock_tasks, 5)

    if not hasattr(openai, 'api_key') or not openai.api_key:
        return get_mock_tasks_reliably()

    # --- DATA FORMATTING FOR THE PROMPT ---
    completed_tasks_str = "\n".join(
        [f"- {task[3]}" for task in path_history.get('completed', [])]) or "None."
    incomplete_tasks_str = "\n".join(
        [f"- {task[3]}" for task in path_history.get('incomplete', [])]) or "None."

    # --- NEW HYPER-DETAILED PROMPT FOR COLLEGE PLANNING ---
    prompt = (
        f"# CONTEXT\n"
        f"You are an expert AI college admissions counselor creating a personalized roadmap for a high school student.\n\n"

        f"# STUDENT PROFILE\n"
        f"- Current Grade: {college_context.get('grade', 'N/A')}\n"
        f"- Current Planning Stage: {college_context.get('planning_stage', 'N/A')}\n"
        f"- Interested Majors: {college_context.get('majors', 'N/A')}\n"
        # <-- ADDED
        f"- Target Colleges: {college_context.get('target_colleges', 'None specified')}\n"
        f"- Current GPA: {user_stats.get('gpa', 'N/A')}\n\n"

        f"# STUDENT HISTORY\n"
        f"## Recently Completed Tasks:\n{completed_tasks_str}\n\n"
        f"## Recently Incomplete or Failed Tasks:\n{incomplete_tasks_str}\n\n"

        f"# YOUR TASK\n"
        f"Generate a new, 5-step college planning roadmap based on all the context provided.\n\n"

        f"# CRITICAL RULES\n"
        f"- Your ENTIRE output must be a single, raw JSON object. Do not include any text, explanations, or markdown formatting.\n"
        f"- The plan must contain exactly 5 task objects.\n"
        f"- The tasks must be novel and not repeat tasks from the student's history.\n"
        f"- The plan must be appropriate for the student's grade level and current planning stage.\n\n"

        f"# JSON SCHEMA\n"
        f"Your output must conform to this exact structure:\n"
        f"{{\n"
        f'  "tasks": [\n'
        f'    {{\n'
        f'      "description": "A string describing the specific, actionable task.",\n'
        f'      "type": "A string, either \'standard\' or \'milestone\'.",\n'
        f'      "stat_to_update": "A string if type is \'milestone\' (e.g., \'essay_progress\', \'applications_submitted\', \'colleges_researched\'), otherwise null.",\n'
        f'      "category": "This MUST be the string \'College Planning\'."\n'
        f'    }}\n'
        f'  ]\n'
        f'}}'
    )

    try:
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant that responds only in perfectly formatted JSON."},
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
        print(
            f"\n--- OPENAI API ERROR IN _get_college_planning_ai_tasks: {e} ---\n")
        return get_mock_tasks_reliably()


def _get_college_planning_ai_chat_response(history, user_stats):
    """Generates a proactive and context-aware chat response for college planning."""
    if not hasattr(openai, 'api_key') or not openai.api_key:
        return "I'm in testing mode, but I'm saving our conversation!"

    college_info = user_stats.get("college_path", {})
    system_message = {
        "role": "system",
        "content": (
            "You are a friendly and proactive college planning advisor. The student is in "
            f"grade {college_info.get('grade', 'N/A')} and is in the '{college_info.get('planning_stage', 'N/A')}' stage. "
            "If the conversation is just beginning, greet the user and ask what specific part of college planning they want to discuss (e.g., essays, applications, college lists). "
            "In subsequent messages, be an encouraging and helpful advisor."
        )
    }
    messages = [system_message] + history
    try:
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo", messages=messages)
        return completion.choices[0].message.content
    except Exception as e:
        print(
            f"\n--- OPENAI API ERROR IN _get_college_planning_ai_chat_response: {e} ---\n")
        return "Sorry, I encountered an error connecting to the AI."


def _generate_and_save_new_college_path(user_id, college_context):
    """
    Gathers all context, generates, and saves a new college planning path.
    This function mirrors the robust logic of the test prep version.
    """
    try:
        # 1. --- GATHER FULL CONTEXT ---
        # Get the user's academic stats (GPA, test scores, etc.)
        user_record = db.select("users", where={"id": user_id})
        if not user_record:
            raise ValueError(f"User with ID {user_id} not found.")
        user_stats = json.loads(user_record[0][3])

        # Get the user's chat history from the session
        chat_history = session.get('chat_history', [])

        # Get the user's previous College Planning tasks to use as history
        all_college_tasks = db.select(
            "paths", where={"user_id": user_id, "category": "College Planning"})
        path_history = {
            # is_completed is column 4
            "completed": [task for task in all_college_tasks if task[4]],
            "incomplete": [task for task in all_college_tasks if not task[4]]
        }

        # 2. --- DEACTIVATE OLD PATH ---
        # This preserves history by marking old tasks as inactive instead of deleting them.
        db.update("paths", {"is_active": False}, where={
                  "user_id": user_id, "category": "College Planning"})

        # 3. --- GENERATE NEW TASKS ---
        # Call the AI helper with all the rich context we've gathered
        tasks = _get_college_planning_ai_tasks(
            college_context, user_stats, path_history)

        if not tasks or len(tasks) != 5:
            raise ValueError(
                "AI task generation did not return the expected 5 tasks.")

        # 4. --- SAVE NEW TASKS ---
        saved_tasks = []
        for i, task_data in enumerate(tasks):
            task_id = db.insert("paths", {
                "user_id": user_id,
                "task_order": i + 1,
                "description": task_data.get("description"),
                "type": task_data.get("type"),
                "stat_to_update": task_data.get("stat_to_update"),
                "category": "College Planning",  # Hardcode the correct category
                "is_active": True,
                "is_completed": False
            })
            # Return the full task data, including the new database ID
            saved_tasks.append(
                {**task_data, "id": task_id, "is_completed": False})

        return saved_tasks

    except Exception as e:
        print(f"Error in _generate_and_save_new_college_path: {e}")
        return []  # Return an empty list if anything goes wrong


@app.route("/dashboard/college-path-builder", methods=["GET", "POST"])
@login_required
def college_path_builder():
    user = User.from_session(db, session)
    if not user:
        return redirect(url_for('login'))

    stats = user.get_stats()
    college_stats = stats.get('college_path', {})

    if request.method == "POST":
        # Collect all context from the form, including the new field
        college_context = {
            'grade': request.form.get('current_grade'),
            'planning_stage': request.form.get('planning_stage'),
            'majors': request.form.get('interested_majors'),
            # <-- ADDED
            'target_colleges': request.form.get('target_colleges', '')
        }
        # Save the context to the user's profile
        stats['college_path'] = college_context
        user.set_stats(stats)

        # Generate the first path for the user
        _generate_and_save_new_college_path(user.data[0], college_context)

        # Go to the view page
        return redirect(url_for('college_path_view'))

    # For GET requests, render the builder page with existing data
    return render_template(
        "college_path_builder.html",
        **college_stats
    )


@app.route('/dashboard/college-path-view')
@login_required
def college_path_view():
    return render_template("college_path_view.html")


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
    all_tasks = db.select("paths", where={"user_id": user_id})

    # Test Prep Counts
    active_test_tasks = [t for t in all_tasks if t[5] and t[9] == 'Test Prep']
    test_prep_completed_current = sum(1 for t in active_test_tasks if t[4])
    total_test_prep_completed = sum(
        1 for t in all_tasks if t[4] and t[9] == 'Test Prep')

    # College Planning Counts
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
    user_id = user.data[0]
    all_tasks = db.select("paths", where={"user_id": user_id})

    # Test Prep Counts
    active_test_tasks = [t for t in all_tasks if t[5] and t[9] == 'Test Prep']
    test_prep_completed = sum(1 for t in active_test_tasks if t[4])
    test_prep_upcoming = 5 - test_prep_completed
    total_test_prep_completed = sum(
        1 for t in all_tasks if t[4] and t[9] == 'Test Prep')

    # College Planning Counts
    active_college_tasks = [
        t for t in all_tasks if t[5] and t[9] == 'College Planning']
    college_planning_completed_current = sum(
        1 for t in active_college_tasks if t[4])
    total_college_planning_completed = sum(
        1 for t in all_tasks if t[4] and t[9] == 'College Planning')

    return render_template(
        "stats.html",
        test_prep_completed=test_prep_completed,
        test_prep_upcoming=test_prep_upcoming,
        total_test_prep_completed=total_test_prep_completed,
        college_planning_completed_current=college_planning_completed_current,
        total_college_planning_completed=total_college_planning_completed,
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
    user = User.from_session(db, session)
    if not user:
        return redirect(url_for("login"))

    user_id = user.data[0]
    all_tasks = db.select(
        "paths", where={"user_id": user_id}, order_by="created_at DESC")
    stats = user.get_stats()

    # Process tasks into generations
    test_prep_generations = {}
    college_planning_generations = {}

    for task in all_tasks:
        # Using created_at (column 6) as a generation key
        generation_key = task[6]
        category = task[9]

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


@app.route('/api/college-path-status')
@login_required
def college_path_status():
    """Checks if a user has an active College Planning path."""
    user = User.from_session(db, session)
    if not user:
        return jsonify({"has_path": False, "error": "User not found"}), 404

    user_id = user.data[0]
    active_tasks = db.select(
        "paths", where={"user_id": user_id, "is_active": True, "category": "College Planning"})

    return jsonify({"has_path": bool(active_tasks)})


# --- API ROUTES FOR THE PATH BUILDER (Fixed) ---

@app.route("/api/tasks", methods=['GET', 'POST'])
@login_required
def api_tasks():
    user = User.from_session(db, session)
    user_id = user.data[0]
    stats = user.get_stats()
    # NEW: Determine the category from the request URL
    category = request.args.get('category', 'Test Prep')

    try:
        # UPDATED: Filter tasks by the specific category
        active_path = db.select(
            "paths", where={"user_id": user_id, "is_active": True, "category": category})

        if request.method == "POST" or not active_path:
            if active_path:
                db.update("paths", {"is_active": False},
                          where={"user_id": user_id, "category": category})

            # NEW: Call the correct generator based on the category
            if category == 'College Planning':
                college_context = stats.get("college_path", {})
                tasks = _generate_and_save_new_college_path(
                    user_id, college_context)
            else:  # Default to Test Prep
                test_path_info = stats.get("test_path", {})
                strengths = test_path_info.get("strengths", "general studying")
                weaknesses = test_path_info.get(
                    "weaknesses", "test-taking skills")
                tasks = _generate_and_save_new_test_path(
                    user_id, strengths, weaknesses)
            return jsonify(tasks)

        if active_path:
            active_path = sorted(active_path, key=lambda x: x[2])
            tasks = [{
                "id": row[0],
                "description": row[3],
                "is_completed": bool(row[4]),
                "type": row[7],
                "stat_to_update": row[8]
            } for row in active_path]
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
        # NEW: Find the task to determine its category before regenerating
        task_info = db.select(
            "paths", where={"id": task_id, "user_id": user_id})
        if not task_info:
            return jsonify({"success": False, "error": "Task not found"}), 404

        category = task_info[0][9]  # category is the 10th column (index 9)
        stats = user.get_stats()

        if category == 'College Planning':
            college_context = stats.get("college_path", {})
            new_tasks = _generate_and_save_new_college_path(
                user_id, college_context)
        else:  # Default to Test Prep
            test_path_info = stats.get("test_path", {})
            strengths = test_path_info.get("strengths", "general studying")
            weaknesses = test_path_info.get("weaknesses", "test-taking skills")
            new_tasks = _generate_and_save_new_test_path(
                user_id, strengths, weaknesses)

        return jsonify({"success": True, "tasks": new_tasks})

    elif status == 'complete' and task_id:
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
    category = request.args.get(
        'category', 'Test Prep')  # Read category from URL

    if not history or (len(history) == 1 and history[0]['role'] == 'user' and history[0]['content'] == 'INITIAL_MESSAGE'):
        history = []

    # NEW: Call the correct AI chat helper based on the category
    if category == 'College Planning':
        reply = _get_college_planning_ai_chat_response(history, stats)
    else:
        reply = _get_test_prep_ai_chat_response(history, stats)

    history.append({"role": "assistant", "content": reply})
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
