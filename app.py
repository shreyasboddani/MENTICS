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
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from authlib.integrations.flask_client import OAuth
from werkzeug.utils import secure_filename

# Explicitly load the .env file from the correct path
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
# --- START: UPLOAD FOLDER CONFIGURATION ---
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.url_map.strict_slashes = False
app.permanent_session_lifetime = timedelta(minutes=10)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
# --- END: UPLOAD FOLDER CONFIGURATION ---


oauth = OAuth(app)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    client_kwargs={'scope': 'openid email profile'}
)


def init_db():
    db.create_table("users", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "email": "TEXT NOT NULL UNIQUE",
        "password": "TEXT NOT NULL",
        "stats": "TEXT NOT NULL",
        "name": "TEXT NOT NULL DEFAULT ''",
        "onboarding_completed": "BOOLEAN DEFAULT FALSE",
        "onboarding_data": "TEXT",
        "profile_picture": "TEXT"
    })
    db.add_column("users", "name", "TEXT NOT NULL DEFAULT ''")
    db.add_column("users", "onboarding_completed", "BOOLEAN DEFAULT FALSE")
    db.add_column("users", "onboarding_data", "TEXT")
    db.add_column("users", "profile_picture", "TEXT")

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
        "category": "TEXT",
        "due_date": "TEXT",
        "is_user_added": "BOOLEAN DEFAULT FALSE",
        "reason": "TEXT"
    })
    db.create_table("subtasks", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "parent_task_id": "INTEGER NOT NULL",
        "description": "TEXT NOT NULL",
        "is_completed": "BOOLEAN DEFAULT FALSE",
        "FOREIGN KEY(parent_task_id)": "REFERENCES paths(id) ON DELETE CASCADE"
    })
    db.create_table("stat_history", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id": "INTEGER NOT NULL",
        "stat_name": "TEXT NOT NULL",
        "stat_value": "TEXT NOT NULL",
        "recorded_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    })
    db.create_table("chat_conversations", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id": "INTEGER NOT NULL",
        "category": "TEXT NOT NULL",
        "history": "TEXT NOT NULL",
        "UNIQUE": "(user_id, category)"
    })
    # NEW: Table to store recent user activities
    db.create_table("activity_log", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id": "INTEGER NOT NULL",
        # e.g., 'task_completed', 'path_generated', 'stat_updated'
        "activity_type": "TEXT NOT NULL",
        # JSON string with context like task name, stat name, etc.
        "details": "TEXT",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    })
    # NEW: Table for gamification stats
    db.create_table("gamification_stats", {
        "user_id": "INTEGER PRIMARY KEY",
        "points": "INTEGER DEFAULT 0",
        "current_streak": "INTEGER DEFAULT 0",
        "last_completed_date": "TEXT",
        "FOREIGN KEY(user_id)": "REFERENCES users(id) ON DELETE CASCADE"
    })
    # NEW: Table for forum posts (threads)
    db.create_table("forum_posts", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id": "INTEGER NOT NULL",
        "user_name": "TEXT NOT NULL",
        "title": "TEXT NOT NULL",
        "content": "TEXT NOT NULL",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "FOREIGN KEY(user_id)": "REFERENCES users(id) ON DELETE CASCADE"
    })
    # NEW: Table for forum replies
    db.create_table("forum_replies", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "post_id": "INTEGER NOT NULL",
        "user_id": "INTEGER NOT NULL",
        "user_name": "TEXT NOT NULL",
        "content": "TEXT NOT NULL",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "FOREIGN KEY(post_id)": "REFERENCES forum_posts(id) ON DELETE CASCADE",
        "FOREIGN KEY(user_id)": "REFERENCES users(id) ON DELETE CASCADE"
    })


# --- HELPER FUNCTIONS ---


def log_activity(user_id, activity_type, details={}):
    """Helper function to log user activities into the database."""
    db.insert("activity_log", {
        "user_id": user_id,
        "activity_type": activity_type,
        "details": json.dumps(details)
    })

# NEW: Helper to get tracker data for prompts


def _get_stat_history_for_prompt(user_id):
    """Fetches and formats a summary of the user's stat history for AI prompts."""
    history_records = db.select(
        "stat_history", where={"user_id": user_id}, order_by="recorded_at DESC LIMIT 20")
    if not history_records:
        return "No historical performance data available yet."

    summary = []
    for record in history_records:
        stat_name, stat_value, recorded_at = record['stat_name'], record['stat_value'], record['recorded_at']
        date = recorded_at.split(" ")[0]
        # Make stat names more readable
        readable_name = stat_name.replace('_', ' ').title()
        summary.append(
            f"- On {date}, their {readable_name} was recorded as {stat_value}.")
    return "\n".join(summary)


# --- DECORATORS & FILTERS ---


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        user = User.from_session(db, session)
        if user is None:
            session.clear()
            return redirect(url_for("login"))
        # Pass the user object to the decorated function
        kwargs['user'] = user
        return f(*args, **kwargs)
    return decorated_function


@app.template_filter('format_date')
def format_date_filter(s):
    if not s:
        return ""
    try:
        # Use the user's timezone from the session, with a fallback to UTC
        user_tz_str = session.get('timezone', 'UTC')
        user_tz = ZoneInfo(user_tz_str)

        naive_dt = datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
        utc_dt = naive_dt.replace(tzinfo=ZoneInfo("UTC"))
        user_local_dt = utc_dt.astimezone(user_tz)
        # More readable format e.g., Jan 01, 2024
        return user_local_dt.strftime('%b %d, %Y')
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        # Fallback for just the date part if parsing fails
        return s.split(' ')[0]

# NEW: Jinja2 filter to display relative time


@app.template_filter('time_ago')
def time_ago_filter(s):
    if not s:
        return ""
    try:
        naive_dt = datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
        utc_dt = naive_dt.replace(tzinfo=ZoneInfo("UTC"))
        now = datetime.now(ZoneInfo("UTC"))
        diff = now - utc_dt

        seconds = diff.total_seconds()
        if seconds < 60:
            return "just now"
        minutes = seconds / 60
        if minutes < 60:
            return f"{int(minutes)}m ago"
        hours = minutes / 60
        if hours < 24:
            return f"{int(hours)}h ago"
        days = hours / 24
        return f"{int(days)}d ago"
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        return s.split(' ')[0]

# --- AI HELPER FUNCTIONS (UPDATED) ---


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


def _get_test_prep_ai_tasks(strengths, weaknesses, user_stats={}, chat_history=[], path_history={}, stat_history=""):
    """Generates hyper-intelligent, adaptive test prep tasks with a detailed, gamified prompt."""

    def get_mock_tasks_reliably():
        print("--- DEBUG: Running corrected Test Prep mock generator. ---")
        all_mock_tasks = [
            {"description": "Take a full-length, timed SAT practice test.", "reason": "This is a 'boss battle' to test your skills under pressure and identify areas for improvement.",
                "type": "milestone", "stat_to_update": "sat_total", "category": "Test Prep", "difficulty": "hard"},
            {"description": "Review algebra concepts from your SAT practice test.", "reason": "Understanding algebra is crucial for a high score on the math section.",
                "type": "standard", "stat_to_update": None, "category": "Test Prep", "difficulty": "medium"},
            {"description": "Practice 15 difficult vocabulary words.", "reason": "A strong vocabulary will help you tackle the reading and writing sections with confidence.",
                "type": "standard", "stat_to_update": None, "category": "Test Prep", "difficulty": "easy"},
            {"description": "Take a timed ACT Science practice section.", "reason": "This will help you get used to the pace of the science section and improve your time management.",
                "type": "milestone", "stat_to_update": "act_science", "category": "Test Prep", "difficulty": "hard"},
            {"description": "Work on time management strategies for the reading section.", "reason": "Finishing the reading section on time is a common challenge. Practicing strategies will improve your score.",
                "type": "standard", "stat_to_update": None, "category": "Test Prep", "difficulty": "medium"}
        ]
        return random.sample(all_mock_tasks, 5)

    if not os.getenv("GEMINI_API_KEY"):
        return get_mock_tasks_reliably()

    completed_tasks_str = "\n".join(
        [f"- {task['description']}" for task in path_history.get('completed', [])]) or "None."
    incomplete_tasks_str = "\n".join(
        [f"- {task['description']}" for task in path_history.get('incomplete', [])]) or "None."
    chat_history_str = "\n".join(
        [f"{msg['role'].capitalize()}: {msg['content']}" for msg in chat_history]) or "No conversation history yet."
    latest_user_message = next((msg['content'] for msg in reversed(
        chat_history) if msg['role'] == 'user'), "N/A")

    test_date_info = "Not set by the student."
    test_date_str = user_stats.get("test_path", {}).get("test_date")
    if test_date_str:
        try:
            user_tz_str = session.get('timezone', 'UTC')
            try:
                user_tz = ZoneInfo(user_tz_str)
            except ZoneInfoNotFoundError:
                user_tz = ZoneInfo("UTC")

            test_date = datetime.strptime(test_date_str, '%Y-%m-%d')
            delta = test_date.replace(tzinfo=user_tz) - datetime.now(user_tz)
            formatted_date = test_date.strftime('%B %d, %Y')
            if delta.days >= 0:
                test_date_info = f"on {formatted_date} ({delta.days} days remaining)"
            else:
                test_date_info = f"on {formatted_date} (this date has passed)"
        except ValueError:
            test_date_info = "in an invalid format."

    prompt = (
        f"# MISSION\n"
        f"You are an elite AI test prep coach for the Mentics platform. Your mission is to generate an intelligent, 5-step study plan that is precisely tailored to the student's evolving needs. The plan must be a logical continuation of their journey, demonstrating a deep understanding of their history and current context.\n\n"

        f"## CRITICAL SCENARIO ANALYSIS (ACTION REQUIRED)\n"
        f"First, determine the student's current situation and choose your generation strategy:\n"
        f"1.  **Regeneration Request:** If the most recent user message (see below) contains keywords like 'regenerate', 'new path', 'change', or expresses a desire for a different approach (e.g., 'the test is tomorrow!'), your **highest priority** is to generate a path that directly addresses that immediate request. The new plan MUST reflect the specific needs mentioned in that message.\n"
        f"2.  **Post-Path Continuation:** If the student has just completed all tasks in their previous path, the new plan MUST be a logical next step. For example, if they just finished a pre-test path, the new path should focus on analyzing their scores, identifying new weaknesses from the test, and planning long-term improvements. DO NOT simply assign more practice.\n"
        f"3.  **Standard Generation:** If neither of the above applies, generate a standard path that builds upon their history and addresses their stated goals.\n\n"

        f"# STUDENT ANALYSIS DATA\n"
        f"- Strengths: {strengths}\n"
        f"- Weaknesses: {weaknesses}\n"
        f"- Test Date: {test_date_info}\n"
        f"- Current SAT Scores: Math {user_stats.get('sat_math', 'N/A')}, EBRW {user_stats.get('sat_ebrw', 'N/A')}\n"
        f"- Current ACT Scores: Math {user_stats.get('act_math', 'N/A')}, Reading {user_stats.get('act_reading', 'N/A')}, Science {user_stats.get('act_science', 'N/A')}\n\n"

        f"## HISTORICAL & CONVERSATIONAL CONTEXT\n"
        f"This is CRITICAL for creating an intelligent, continuous learning journey.\n"
        f"- **Most Recent User Request:** '{latest_user_message}' <== **If this is a regeneration request, it takes precedence over all other data.**\n"
        f"- Recently Completed Tasks: {completed_tasks_str}\n"
        f"- Incomplete Tasks from Previous Path: {incomplete_tasks_str}\n"
        f"- Full Conversation History: {chat_history_str}\n"
        f"- Historical Performance Data (Tracker):\n{stat_history}\n\n"

        f"# YOUR TASK: GENERATE THE NEW 5-STEP PLAN\n"
        f"Based on your scenario analysis and all student data, generate a new 5-step study plan. Each task must:\n"
        f"- Be specific, actionable, and include a markdown link to a high-quality, free resource (Khan Academy, official practice tests, specific YouTube tutorials).\n"
        f"- Include a mix of task types: at least one **Resource Task** (e.g., 'Watch a video'), one **Practice Task** (e.g., 'Complete a quiz'), and one **Strategic Task** (e.g., 'Develop a new timing strategy').\n"
        f"- Have an assigned difficulty for gamification purposes.\n\n"

        f"# CRITICAL DIRECTIVES & JSON SCHEMA\n"
        f"1.  **JSON Output ONLY**: Your entire output MUST be a single, raw JSON object. No extra text.\n"
        f"2.  **Adaptive Focus**: If context shows a focus on SAT or ACT, all tasks must target that test. Never mix.\n"
        f"3.  **Meaningful Milestones**: Use 'milestone' only for major assessments (e.g., a full practice test). `stat_to_update` must be null for 'standard' tasks.\n"
        f"4.  **Correct Stat Naming**: For milestones, `stat_to_update` must be one of: ['sat_math', 'sat_ebrw', 'sat_total', 'act_math', 'act_reading', 'act_science', 'act_composite'].\n"
        f"5.  **Intelligent 'Boss Battles'**: A 'Boss Battle' is a major milestone, like a full practice test. It should be the culmination of the preceding tasks. The description for such a task MUST begin with 'Boss Battle:'. Use these strategically every 2-3 paths to assess progress.\n"
        f"6.  **SAT Math & Desmos**: If SAT Math is a weakness, at least one task MUST focus on using the Desmos calculator as a strategic tool.\n\n"

        f"# JSON OUTPUT STRUCTURE\n"
        f"{{\n"
        f'  "tasks": [\n'
        f'    {{\n'
        f'      "description": "Specific, actionable task with a markdown link, like [this resource](https://example.com).",\n'
        f'      "reason": "A brief, motivating explanation for this task.",\n'
        f'      "type": "Either \'standard\' or \'milestone\'.",\n'
        f'      "stat_to_update": "A valid stat name (string) ONLY if type is milestone, otherwise null.",\n'
        f'      "category": "This MUST be the string \'Test Prep\'.",\n'
        f'      "difficulty": "Either \'easy\' (10 points), \'medium\' (25 points), or \'hard\' (50 points). Boss Battles should be \'epic\' (100 points)."\n'
        f'    }}\n'
        f'    // ... (four more task objects)\n'
        f'  ]\n'
        f'}}'
    )
    try:
        model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config={"response_mime_type": "application/json"}
        )
        response = model.generate_content(prompt)
        response_data = json.loads(response.text)
        tasks = response_data.get("tasks", [])
        if isinstance(tasks, list) and len(tasks) > 0:
            return tasks
        raise ValueError("Invalid format from AI")
    except Exception as e:
        print(f"\n--- GEMINI API ERROR IN _get_test_prep_ai_tasks: {e} ---\n")
        return get_mock_tasks_reliably()


def _get_test_prep_ai_chat_response(history, user_stats, stat_history="", user_id=None):
    if not os.getenv("GEMINI_API_KEY"):
        return "I'm in testing mode, but I'm saving our conversation!"

    # Extract test date info
    test_date_info = "The student has not set a test date yet."
    test_date_str = user_stats.get("test_path", {}).get("test_date")
    if test_date_str:
        try:
            # Use user's timezone for 'now' to get accurate days remaining
            user_tz_str = session.get('timezone', 'UTC')
            try:
                user_tz = ZoneInfo(user_tz_str)
            except ZoneInfoNotFoundError:
                user_tz = ZoneInfo("UTC")

            test_date = datetime.strptime(test_date_str, '%Y-%m-%d')
            delta = test_date.replace(tzinfo=user_tz) - datetime.now(user_tz)
            formatted_date = test_date.strftime('%B %d, %Y')
            if delta.days >= 0:
                test_date_info = f"The student's test is on {formatted_date} ({delta.days} days from now)."
            else:
                test_date_info = f"The student's test date was {formatted_date}, which has already passed."
        except ValueError:
            test_date_info = f"The student has set a test date, but it's in an invalid format: {test_date_str}."

        # Pull additional student data
    strengths = user_stats.get("strengths", "Not provided")
    weaknesses = user_stats.get("weaknesses", "Not provided")
    completed_tasks_str = user_stats.get("completed_tasks", "None")
    incomplete_tasks_str = user_stats.get("incomplete_tasks", "None")

    # Get current active tasks
    current_tasks = "No tasks available." if user_id is None else _get_current_numbered_tasks(
        user_id, "Test Prep")    # Build system message with all context
    system_message = (
        "# MISSION & IDENTITY\n"
        "You are an expert AI assistant for Mentics, a web app that creates personalized learning paths for high school students. Your specific persona is a highly adaptive, intelligent, and supportive SAT/ACT test prep coach. Your personality is encouraging yet focused, guiding students toward steady, measurable progress. You are a supplement to the main 'Path' feature, which visually lays out the student's learning journey.\n\n"

        "# MENTICS APPLICATION CONTEXT\n"
        "To answer user questions accurately, you must understand the app's key features:\n"
        "- **AI Path Generation**: The core of Mentics. The app generates a visual, step-by-step roadmap of tasks for the student to follow for test prep and college planning.\n"
        "- **AI Assistant (Your Role)**: You are the chat interface. You help users when they are stuck on a task, provide encouragement, and offer deeper explanations.\n"
        "- **Stats & Tracker**: A dashboard where users input their scores (GPA, SAT, ACT) and track their progress over time with charts.\n"
        "- **Gamification**: The app includes points and streaks for completing tasks to keep users motivated.\n"
        "- **Forum & Leaderboard**: Social features where users can connect and compete.\n\n"

        f"## CURRENT STUDENT ANALYSIS\n"
        f"This is the specific student you are currently coaching:\n"
        f"- SAT Math: {user_stats.get('sat_math', 'Not provided')}\n"
        f"- SAT EBRW: {user_stats.get('sat_ebrw', 'Not provided')}\n"
        f"- ACT Math: {user_stats.get('act_math', 'Not provided')}\n"
        f"- ACT Reading: {user_stats.get('act_reading', 'Not provided')}\n"
        f"- ACT Science: {user_stats.get('act_science', 'Not provided')}\n"
        f"- GPA: {user_stats.get('gpa', 'Not provided')}\n"
        f"- Test Date Info: {test_date_info}\n"
        f"- Strengths: {strengths}\n"
        f"- Weaknesses: {weaknesses}\n"
        f"- Recently Completed Tasks: {completed_tasks_str}\n"
        f"- Incomplete/Failed Tasks: {incomplete_tasks_str}\n"
        f"- Historical Performance Data (from Tracker): {stat_history}\n"
        f"- Current Active Tasks:\n{current_tasks}\n\n"

        "## CORE COACHING DIRECTIVES (Your Rules of Engagement)\n"
        "0.  **Initial Greeting**: Your very first message to the user *must* be a warm and encouraging welcome. It *must* also clearly state that they can type **'regenerate'** or **'new path'** at any time to get a new path based on your conversation.\n"
        "1.  **Primary Goal: Path & App Support**: Your main purpose is to help the user with their current, active Path. Answer their questions about specific tasks, why they were assigned, and how to approach them. You must also be able to answer general questions about using the Mentics application's features as described above.\n"
        "2.  **Path Regeneration Protocol**: If a user expresses that their goals have changed or they want a different approach, reiterate that they can use the regeneration commands.\n"
        "3.  **Provide High-Quality Resources**: When a student is stuck or asks for help, provide specific, reputable, and free resources using markdown links (e.g., `[Khan Academy](https://...)`, official practice test PDFs, specific educational YouTube videos).\n"
        "4.  **Actionable Focus**: Every response must provide a clear next step, a useful tip, or actionable guidance. Never leave the user wondering what to do next.\n"
        "5.  **Adaptive Response Length**: \n"
        "    - For quick questions, provide short, concise answers KEEP THESE UNDER 100 WORDS).\n"
        "    - For complex requests (e.g., explaining a difficult concept), provide detailed, step-by-step explanations using lists or bullet points KEEP THESE UNDER 250 words.\n"
        "6.  **Proactive and Strategic Guidance**: Offer actionable strategies, study tips, and relevant resources when a user expresses difficulty. Address their weaknesses directly but leverage their strengths to build confidence.\n"
        "7.  **Mentorship Tone**: Always maintain a supportive, motivating, and realistic tone. Your goal is to empower the student and encourage consistent effort and progress."
    )

    # Build Gemini chat history
    gemini_history = []
    for message in history:
        role = "model" if message["role"] == "assistant" else "user"
        gemini_history.append({"role": role, "parts": [message["content"]]})

    try:
        # Initialize model
        model = genai.GenerativeModel(
            'gemini-2.5-flash', system_instruction=system_message)
        chat = model.start_chat(history=gemini_history[:-1])
        last_user_message = gemini_history[-1]['parts'][0] if gemini_history else "Hello"
        response = chat.send_message(last_user_message)
        return response.text
    except Exception as e:
        print(
            f"\n--- GEMINI API ERROR IN _get_test_prep_ai_chat_response: {e} ---\n")
        return "Sorry, I encountered an error connecting to the AI."


def _generate_and_save_new_test_path(user_id, test_path_info, chat_history=[]):
    user_record = db.select("users", where={"id": user_id})
    user_stats = json.loads(user_record[0]['stats']) if user_record else {}
    strengths = test_path_info.get("strengths", "general studying")
    weaknesses = test_path_info.get("weaknesses", "test-taking skills")

    all_tasks = db.select(
        "paths", where={"user_id": user_id, "category": "Test Prep"})
    path_history = {
        "completed": [task for task in all_tasks if task['is_completed']],
        "incomplete": [task for task in all_tasks if not task['is_completed']]
    }

    # Fetch tracker data
    stat_history = _get_stat_history_for_prompt(user_id)

    db.update("paths", {"is_active": False}, where={
              "user_id": user_id, "category": "Test Prep", "is_active": True})

    tasks = _get_test_prep_ai_tasks(strengths, weaknesses,
                                    user_stats, chat_history, path_history, stat_history)
    tasks = tasks[:5]

    saved_tasks = []
    for i, task in enumerate(tasks):
        task_id = db.insert("paths", {
            "user_id": user_id, "task_order": i + 1, "description": task.get("description"),
            "reason": task.get("reason"), "type": task.get("type"), "stat_to_update": task.get("stat_to_update"),
            "category": "Test Prep", "is_active": True, "is_completed": False
        })
        new_task_data = db.select("paths", where={"id": task_id})[0]
        saved_tasks.append({
            "id": new_task_data['id'], "description": new_task_data['description'],
            "reason": new_task_data['reason'], "type": new_task_data['type'],
            "stat_to_update": new_task_data['stat_to_update'], "is_completed": False
        })
    # LOGGING
    log_activity(user_id, 'path_generated', {'category': 'Test Prep'})
    return saved_tasks


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


def _get_college_planning_ai_tasks(college_context, user_stats, path_history, chat_history=[], stat_history=""):
    """Generates hyper-intelligent, adaptive college planning tasks with a detailed, gamified prompt."""

    def get_mock_tasks_reliably():
        print("--- DEBUG: Running corrected College Planning mock generator. ---")
        all_mock_tasks = [
            {"description": "Research 5 colleges that match your interests.", "reason": "Finding the right fit is the first step to a successful college experience.",
                "type": "standard", "stat_to_update": None, "category": "College Planning", "difficulty": "medium"},
            {"description": "Write a rough draft of your Common App personal statement.", "reason": "This is your chance to tell your story and show admissions officers who you are.",
                "type": "milestone", "stat_to_update": "essay_progress", "category": "College Planning", "difficulty": "hard"},
            {"description": "Update your GPA in your profile.", "reason": "Keeping your academic information up-to-date is important for tracking your progress.",
                "type": "milestone", "stat_to_update": "gpa", "category": "College Planning", "difficulty": "easy"},
            {"description": "Request three letters of recommendation from teachers.", "reason": "Strong letters of recommendation can make a big difference in your application.",
                "type": "standard", "stat_to_update": None, "category": "College Planning", "difficulty": "medium"},
            {"description": "Create a spreadsheet to track application deadlines.", "reason": "Staying organized is key to a stress-free application season.",
                "type": "standard", "stat_to_update": None, "category": "College Planning", "difficulty": "easy"}
        ]
        return random.sample(all_mock_tasks, 5)

    if not os.getenv("GEMINI_API_KEY"):
        return get_mock_tasks_reliably()

    completed_tasks_str = "\n".join(
        [f"- {task['description']}" for task in path_history.get('completed', [])]) or "None."
    incomplete_tasks_str = "\n".join(
        [f"- {task['description']}" for task in path_history.get('incomplete', [])]) or "None."
    chat_history_str = "\n".join(
        [f"{msg['role'].capitalize()}: {msg['content']}" for msg in chat_history]) or "No conversation history yet."
    latest_user_message = next((msg['content'] for msg in reversed(
        chat_history) if msg['role'] == 'user'), "N/A")

    prompt = (
        f"# MISSION\n"
        f"You are an expert AI college admissions counselor for the Mentics platform. Your mission is to generate an intelligent, 5-step roadmap that provides a clear, logical, and motivating path for a high school student. The plan must be a thoughtful continuation of their journey, not just a random list of tasks.\n\n"

        f"## CRITICAL SCENARIO ANALYSIS (ACTION REQUIRED)\n"
        f"First, determine the student's current situation and choose your generation strategy:\n"
        f"1.  **Regeneration Request:** If the most recent user message (see below) contains keywords like 'regenerate', 'new path', or expresses a significant change in plans (e.g., 'I want to apply to different schools now'), your **highest priority** is to generate a path that directly addresses that immediate request.\n"
        f"2.  **Post-Path Continuation:** If the student has just completed all tasks in their previous path, the new plan MUST be a logical next step in the college planning process (e.g., moving from 'researching colleges' to 'drafting supplemental essays'). It should feel like a natural progression.\n"
        f"3.  **Standard Generation:** If neither of the above applies, generate a standard path that is appropriate for their grade level and builds upon their historical data.\n\n"

        f"# STUDENT ANALYSIS DATA\n"
        f"- Current Grade: {college_context.get('grade', 'N/A')}\n"
        f"- Stated Planning Stage: {college_context.get('planning_stage', 'N/A')}\n"
        f"- Interested Majors: {college_context.get('majors', 'N/A')}\n"
        f"- Target Colleges: {college_context.get('target_colleges', 'None specified')}\n"
        f"- Current GPA: {user_stats.get('gpa', 'N/A')}\n\n"

        f"## HISTORICAL & CONVERSATIONAL CONTEXT\n"
        f"This is CRITICAL for creating an intelligent, continuous learning journey.\n"
        f"- **Most Recent User Request:** '{latest_user_message}' <== **If this is a regeneration request, it takes precedence over all other data.**\n"
        f"- Recently Completed Tasks: {completed_tasks_str}\n"
        f"- Incomplete Tasks from Previous Path: {incomplete_tasks_str}\n"
        f"- Full Conversation History: {chat_history_str}\n"
        f"- Historical Performance Data (Tracker):\n{stat_history}\n\n"

        f"# YOUR TASK: GENERATE THE NEW 5-STEP ROADMAP\n"
        f"Based on your scenario analysis and all student data, generate a new, 5-step roadmap. Each task must:\n"
        f"- Be specific, actionable, and include a markdown link to a reputable, free resource (e.g., Common App, College Board, financial aid sites, specific articles).\n"
        f"- Include a mix of task types: at least one **Resource Task** (e.g., 'Read this guide'), one **Action Task** (e.g., 'Draft your activity list'), and one **Reflection Task** (e.g., 'Brainstorm essay topics').\n"
        f"- Have an assigned difficulty for gamification purposes.\n\n"
        f"- For anything related to test prep, refer the student to the Test Prep Path and do NOT include test prep tasks here( the testprep is the other path when u click path builder on the mentics dashboard).\n\n"

        f"# CRITICAL DIRECTIVES & JSON SCHEMA\n"
        f"1.  **JSON Output ONLY**: Your entire output MUST be a single, raw JSON object. No extra text.\n"
        f"2.  **Stage-Appropriate Tasks**: Align all tasks to the student's grade level and planning stage. A 9th grader should be exploring, while a 12th grader should be finalizing applications.\n"
        f"3.  **Meaningful Milestones**: Use 'milestone' only for significant achievements (e.g., completing an essay draft, updating GPA, submitting an application). `stat_to_update` must be null for 'standard' tasks.\n"
        f"4.  **Intelligent 'Boss Battles'**: A 'Boss Battle' is a major milestone, like submitting a complete application or finalizing a personal statement. It should be the culmination of the preceding tasks. The description for such a task MUST begin with 'Boss Battle:'. Use these strategically based on the student's grade and timeline.\n\n"

        f"# JSON OUTPUT STRUCTURE\n"
        f"{{\n"
        f'  "tasks": [\n'
        f'    {{\n'
        f'      "description": "Specific, actionable task with a markdown link, like [this resource](https://example.com).",\n'
        f'      "reason": "A brief, motivating explanation for this task.",\n'
        f'      "type": "Either \'standard\' or \'milestone\'.",\n'
        f'      "stat_to_update": "A string (\'gpa\', \'essay_progress\', \'applications_submitted\') ONLY if type is milestone, otherwise null.",\n'
        f'      "category": "This MUST be the string \'College Planning\'.",\n'
        f'      "difficulty": "Either \'easy\' (10 points), \'medium\' (25 points), or \'hard\' (50 points). Boss Battles should be \'epic\' (100 points)."\n'
        f'    }}\n'
        f'    // ... (four more task objects)\n'
        f'  ]\n'
        f'}}'
    )
    try:
        model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config={"response_mime_type": "application/json"}
        )
        response = model.generate_content(prompt)
        response_data = json.loads(response.text)
        tasks = response_data.get("tasks", [])
        if isinstance(tasks, list) and len(tasks) > 0:
            return tasks
        raise ValueError("Invalid format from AI")
    except Exception as e:
        print(
            f"\n--- GEMINI API ERROR IN _get_college_planning_ai_tasks: {e} ---\n")
        return get_mock_tasks_reliably()


def _get_college_planning_ai_chat_response(history, user_stats, stat_history="", user_id=None):
    """Generates a proactive and context-aware chat response for college planning."""
    if not os.getenv("GEMINI_API_KEY"):
        return "I'm in testing mode, but I'm saving our conversation!"

    college_info = user_stats.get("college_path", {})

    # Get current active tasks
    current_tasks = "No tasks available." if user_id is None else _get_current_numbered_tasks(
        user_id, "College Planning")

    # Get current active tasks
    current_tasks = _get_current_numbered_tasks(user_id, "College Planning")

    system_message = (
        "# MISSION & IDENTITY\n"
        "You are an expert AI assistant for Mentics, a web app that creates personalized roadmaps for high school students. Your specific persona is a friendly, intelligent, and highly adaptive college planning advisor. Your personality is encouraging, knowledgeable, and supportive. You are a supplement to the main 'Path' feature, which visually lays out the student's journey.\n\n"

        "# MENTICS APPLICATION CONTEXT\n"
        "To answer user questions accurately, you must understand the app's key features:\n"
        "- **AI Path Generation**: The core of Mentics. The app generates a visual, step-by-step roadmap of tasks for the student to follow for college applications, essays, IT IS ALSO IS A RESOURCE FOR SAT/ACT PREP WITH THE TEST PREP PATH sugest the user use this for their SAT/ ACT planning(THIS CAN BE FOUND ON THE DASHBOARD).\n"
        "- **AI Assistant (Your Role)**: You are the chat interface. You help users when they are stuck on a task, provide encouragement, and offer deeper explanations.\n"
        "- **Stats & Tracker**: A dashboard where users input their scores (GPA, SAT, ACT) and track their progress over time with charts.\n"
        "- **Gamification**: The app includes points and streaks for completing tasks to keep users motivated.\n"
        "- **Forum & Leaderboard**: Social features where users can connect and compete.\n\n"

        f"## CURRENT STUDENT ANALYSIS\n"
        f"This is the specific student you are currently advising:\n"
        f"- SAT Math: {user_stats.get('sat_math', 'Not provided')}\n"
        f"- SAT EBRW: {user_stats.get('sat_ebrw', 'Not provided')}\n"
        f"- ACT Math: {user_stats.get('act_math', 'Not provided')}\n"
        f"- ACT Reading: {user_stats.get('act_reading', 'Not provided')}\n"
        f"- ACT Science: {user_stats.get('act_science', 'Not provided')}\n"
        f"- GPA: {user_stats.get('gpa', 'Not provided')}\n"
        f"- Grade Level: {college_info.get('grade', 'N/A')}\n"
        f"- Current Planning Stage: '{college_info.get('planning_stage', 'N/A')}'\n"
        f"- Interested Majors: {college_info.get('majors', 'None')}\n"
        f"- Target Colleges: {college_info.get('target_colleges', 'None')}\n"
        f"- Recently Completed Tasks: {college_info.get('completed_tasks', 'None')}\n"
        f"- Incomplete/Failed Tasks: {college_info.get('incomplete_tasks', 'None')}\n"
        f"- Historical Performance Data (from Tracker): {stat_history}\n"
        f"- Current Active Tasks (numbered for reference):\n{current_tasks}\n"
        f"- Current Active Tasks:\n{current_tasks}\n"


        "## CORE COACHING DIRECTIVES (Your Rules of Engagement)\n"
        "0.  **Initial Greeting**: Your very first message to the user *must* be a warm and encouraging welcome. It *must* also clearly state that they can type **'regenerate'** or **'new path'** at any time to get a new path based on your conversation.\n"
        "1.  **Primary Goal: Path & App Support**: Your main purpose is to help the user with their current, active Path. Answer their questions about specific tasks, why they were assigned, and how to approach them. You must also be able to answer general questions about using the Mentics application's features as described above.\n"
        "2.  **Path Regeneration Protocol**: If a user expresses that their goals have changed or they want a different approach, reiterate that they can use the regeneration commands.\n"
        "3.  **Provide High-Quality Resources**: When a student is stuck or needs guidance, provide specific, reputable, and free resources using markdown links (e.g., links to the Common App, financial aid websites like FAFSA, or helpful articles on essay writing).\n"
        "4.  **Actionable Guidance**: Every response must give the student a clear next step, a valuable resource, or a concrete action to take. Never leave the user wondering what to do next.\n"
        "5.  **Adaptive Response Length**:\n"
        "    - For simple questions, provide short, concise answers KEEP THESE UNDER 100 WORDS.\n"
        "    - For complex requests (e.g., essay brainstorming, advice on choosing colleges), provide detailed, structured responses using lists or bullet points KEEP THESE UNDER 250 WORDS.\n"
        "6.  **Proactive Advising**: If the student seems stuck on a task like 'write an essay', break it down into smaller, actionable steps (e.g., 'Let's start by brainstorming three key experiences you could write about.').\n"
        "7.  **Mentorship Tone**: Always maintain a supportive, encouraging, and realistic tone to keep the student motivated throughout the often-stressful college application process."
        "8. **Suggest Test Prep Path When Relevant**: If the student mentions standardized tests (SAT/ACT) or seems uncertain about test preparation, proactively suggest they explore the MENTICS Test Prep path for tailored study plans and resources.\n"
    )

    gemini_history = []
    for message in history:
        role = "model" if message["role"] == "assistant" else "user"
        gemini_history.append({"role": role, "parts": [message["content"]]})

    try:
        model = genai.GenerativeModel(
            'gemini-2.5-flash', system_instruction=system_message)
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
        user_stats = json.loads(user_record[0]['stats'])

        all_college_tasks = db.select(
            "paths", where={"user_id": user_id, "category": "College Planning"})
        path_history = {
            "completed": [task for task in all_college_tasks if task['is_completed']],
            "incomplete": [task for task in all_college_tasks if not task['is_completed']]
        }

        # Fetch tracker data
        stat_history = _get_stat_history_for_prompt(user_id)

        db.update("paths", {"is_active": False}, where={
                  "user_id": user_id, "category": "College Planning", "is_active": True})

        tasks = _get_college_planning_ai_tasks(
            college_context, user_stats, path_history, chat_history, stat_history)

        tasks = tasks[:5]

        if not tasks or len(tasks) == 0:
            raise ValueError(
                "AI task generation did not return the expected tasks.")

        saved_tasks = []
        for i, task_data in enumerate(tasks):
            task_id = db.insert("paths", {
                "user_id": user_id, "task_order": i + 1, "description": task_data.get("description"),
                "reason": task_data.get("reason"), "type": task_data.get("type"), "stat_to_update": task_data.get("stat_to_update"),
                "category": "College Planning", "is_active": True, "is_completed": False
            })
            saved_tasks.append(
                {**task_data, "id": task_id, "is_completed": False})

        # LOGGING
        log_activity(user_id, 'path_generated', {
                     'category': 'College Planning'})
        return saved_tasks
    except Exception as e:
        print(f"Error in _generate_and_save_new_college_path: {e}")
        return []

# --- Standard Routes ---


@app.route("/")
def home():
    is_logged_in = "user" in session
    return render_template("index.html", is_logged_in=is_logged_in)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        name = request.form["name"]
        password = generate_password_hash(request.form["password"])
        try:
            user_id = db.insert("users", {
                "email": email, "password": password, "name": name,
                "stats": json.dumps({
                    "sat_ebrw": "", "sat_math": "", "act_math": "",
                    "act_reading": "", "act_science": "", "gpa": "", "milestones": 0
                })
            })
            # Initialize gamification stats for new user
            db.insert("gamification_stats", {
                      "user_id": user_id, "points": 0, "current_streak": 0})

            session["user"] = email
            session["user_id"] = user_id
            session.permanent = True
            return redirect(url_for("onboarding"))
        except Exception as e:
            print(f"Signup error: {e}")
            return render_template("signup.html", error="Email already exists!")
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("dashboard"))
    error = None
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user_record_list = db.select("users", where={"email": email})
        if user_record_list:
            user_record = user_record_list[0]
            if check_password_hash(user_record['password'], password):
                session["user"] = user_record['email']
                session["user_id"] = user_record['id']
                session.permanent = True
                return redirect(url_for("dashboard"))
        error = "Invalid credentials"
    return render_template("login.html", error=error)

# NEW: Google Login Route


@app.route('/google-login')
def google_login():
    redirect_uri = url_for('authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

# NEW: Google Authorize Route (Callback) - UPDATED


@app.route('/authorize')
def authorize():
    token = oauth.google.authorize_access_token()
    # The 'nonce' is retrieved from the session and passed to the parse_id_token method
    user_info = oauth.google.parse_id_token(token, nonce=session.get('nonce'))

    # Check if user exists
    user_record_list = db.select("users", where={"email": user_info['email']})

    if user_record_list:
        # User exists, log them in
        user_record = user_record_list[0]
        session["user"] = user_record['email']
        session["user_id"] = user_record['id']
        session.permanent = True
    else:
        # New user, create an account
        # We use a placeholder for the password hash as they'll log in via Google
        password_hash = generate_password_hash(os.urandom(16).hex())
        user_id = db.insert("users", {
            "email": user_info['email'],
            "name": user_info['name'],
            "password": password_hash,
            "stats": json.dumps({
                "sat_ebrw": "", "sat_math": "", "act_math": "",
                "act_reading": "", "act_science": "", "gpa": "", "milestones": 0
            })
        })
        # Initialize gamification stats for new Google user
        db.insert("gamification_stats", {
                  "user_id": user_id, "points": 0, "current_streak": 0})

        session["user"] = user_info['email']
        session["user_id"] = user_id
        session.permanent = True

    return redirect(url_for("onboarding"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route('/onboarding', methods=['GET', 'POST'])
@login_required
def onboarding(user):
    if user.data['onboarding_completed']:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        onboarding_data = {
            'goal': request.form.get('goal'),
            'learning_style': request.form.get('learning_style'),
            'anxieties': request.form.get('anxieties')
        }
        db.update('users', {
            'onboarding_data': json.dumps(onboarding_data),
            'onboarding_completed': True
        }, {'id': user.data['id']})
        return redirect(url_for('dashboard'))

    return render_template('onboarding.html')

# NEW: Add a route to set the user's timezone in the session


@app.route('/set-timezone', methods=['POST'])
def set_timezone():
    data = request.get_json()
    timezone = data.get('timezone')
    if timezone:
        try:
            # Validate that it's a real timezone
            ZoneInfo(timezone)
            session['timezone'] = timezone
            return jsonify({"success": True})
        except ZoneInfoNotFoundError:
            return jsonify({"success": False, "error": "Invalid timezone"}), 400
    return jsonify({"success": False, "error": "Timezone not provided"}), 400

# --- Dashboard & Path Routes ---


@app.route("/dashboard")
@login_required
def dashboard(user):
    if not user.data['onboarding_completed']:
        return redirect(url_for('onboarding'))
    stats = user.get_stats()
    user_id = user.data['id']
    name = user.get_name()
    all_tasks = db.select("paths", where={"user_id": user_id})

    # Get proactive suggestion
    suggestion = _get_proactive_ai_suggestions(user)

    # --- Gamification Stats ---
    gamification_stats_list = db.select(
        "gamification_stats", where={"user_id": user_id})
    if not gamification_stats_list:
        # Fallback to create stats if they don't exist for some reason
        db.insert("gamification_stats", {
                  "user_id": user_id, "points": 0, "current_streak": 0})
        gamification_stats_list = db.select(
            "gamification_stats", where={"user_id": user_id})

    gamification_stats = gamification_stats_list[0]

    game_stats = {
        "points": gamification_stats['points'],
        "streak": gamification_stats['current_streak']
    }

    # --- Progress Calculations ---
    active_test_tasks = [
        t for t in all_tasks if t['is_active'] and t['category'] == 'Test Prep']
    test_prep_completed_current = sum(
        1 for t in active_test_tasks if t['is_completed'])
    total_test_prep_completed = sum(
        1 for t in all_tasks if t['is_completed'] and t['category'] == 'Test Prep')

    active_college_tasks = [
        t for t in all_tasks if t['is_active'] and t['category'] == 'College Planning']
    college_planning_completed_current = sum(
        1 for t in active_college_tasks if t['is_completed'])
    total_college_planning_completed = sum(
        1 for t in all_tasks if t['is_completed'] and t['category'] == 'College Planning')

    # --- Key Stat Calculations ---
    sat_ebrw = stats.get("sat_ebrw")
    sat_math = stats.get("sat_math")
    sat_total = None
    if sat_ebrw and sat_math:
        try:
            sat_total = int(sat_ebrw) + int(sat_math)
        except (ValueError, TypeError):
            sat_total = None

    act_scores = []
    if stats.get("act_math"):
        act_scores.append(int(stats.get("act_math")))
    if stats.get("act_reading"):
        act_scores.append(int(stats.get("act_reading")))
    if stats.get("act_science"):
        act_scores.append(int(stats.get("act_science")))

    act_average = round(sum(act_scores) / len(act_scores)
                        ) if act_scores else None

    # --- Recent Activity Fetch ---
    recent_activities_raw = db.select(
        "activity_log",
        where={"user_id": user_id},
        order_by="created_at DESC LIMIT 5"
    )
    recent_activities = []
    for activity in recent_activities_raw:
        details = json.loads(activity['details'])
        recent_activities.append({
            "type": activity['activity_type'],
            "details": details,
            "timestamp": activity['created_at']
        })

    # --- Data for Activity Chart (UPDATED FOR TIMEZONE) ---
    user_tz_str = session.get('timezone', 'UTC')
    try:
        user_tz = ZoneInfo(user_tz_str)
    except ZoneInfoNotFoundError:
        user_tz = ZoneInfo("UTC")

    today = datetime.now(user_tz).date()
    seven_days_ago = today - timedelta(days=6)
    activity_counts = {(seven_days_ago + timedelta(days=i)
                        ).strftime('%a'): 0 for i in range(7)}
    recent_logs = db.execute(
        "SELECT created_at FROM activity_log WHERE user_id = ? AND date(created_at) >= ?",
        (user_id, seven_days_ago.strftime('%Y-%m-%d'))
    )
    if recent_logs:
        for log in recent_logs:
            utc_dt = datetime.strptime(
                log['created_at'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=ZoneInfo("UTC"))
            user_local_dt = utc_dt.astimezone(user_tz)
            log_date_str = user_local_dt.strftime('%a')
            if log_date_str in activity_counts:
                activity_counts[log_date_str] += 1
    activity_data = {
        "labels": list(activity_counts.keys()),
        "data": list(activity_counts.values())
    }

    # --- Upcoming Test Date Logic ---
    test_date_info = {
        "days_left": None,
        "date_str": None,
        "test_type": None
    }
    test_path_stats = stats.get("test_path", {})
    if test_path_stats.get("test_date"):
        try:
            test_date = datetime.strptime(
                test_path_stats["test_date"], '%Y-%m-%d').date()
            # Use user's timezone for 'today' to ensure accurate countdown
            try:
                user_tz_str = session.get('timezone', 'UTC')
                user_today = datetime.now(ZoneInfo(user_tz_str)).date()
            except ZoneInfoNotFoundError:
                user_today = date.today()  # Fallback to server date
            days_left = (test_date - user_today).days
            if days_left >= 0:
                test_date_info["days_left"] = days_left
                test_date_info["date_str"] = test_date.strftime('%B %d, %Y')
                if test_path_stats.get("desired_sat"):
                    test_date_info["test_type"] = "SAT"
                elif test_path_stats.get("desired_act"):
                    test_date_info["test_type"] = "ACT"
        except (ValueError, TypeError):
            pass

    # --- EXPANDED Achievements Logic ---
    all_achievements = [
        {"id": "pioneer_test", "icon": "🚀", "title": "Test Prep Pioneer",
            "description": "Generated your first Test Prep path.", "is_earned": False},
        {"id": "planner_college", "icon": "🏛️", "title": "College Planner",
            "description": "Generated your first College Planning path.", "is_earned": False},
        {"id": "first_step", "icon": "✅", "title": "First Step",
            "description": "Completed your first task.", "is_earned": False},
        {"id": "task_master_10", "icon": "🔥", "title": "Task Master",
            "description": "Completed 10 tasks.", "is_earned": False},
        {"id": "pathfinder_pro_25", "icon": "🏆", "title": "Pathfinder Pro",
            "description": "Completed 25 tasks.", "is_earned": False},
        {"id": "streak_3", "icon": "⚡", "title": "On a Roll",
            "description": "Maintained a 3-day streak.", "is_earned": False},
        {"id": "streak_7", "icon": "🌟", "title": "Committed",
            "description": "Maintained a 7-day streak.", "is_earned": False},
        {"id": "points_100", "icon": "💯", "title": "Point Collector",
            "description": "Earned 100 points.", "is_earned": False},
        {"id": "points_500", "icon": "💎", "title": "Point Pro",
            "description": "Earned 500 points.", "is_earned": False}
    ]

    all_completed_tasks = total_test_prep_completed + total_college_planning_completed

    # Check which achievements are earned
    if any(t['category'] == 'Test Prep' for t in all_tasks):
        all_achievements[0]['is_earned'] = True
    if any(t['category'] == 'College Planning' for t in all_tasks):
        all_achievements[1]['is_earned'] = True
    if all_completed_tasks >= 1:
        all_achievements[2]['is_earned'] = True
    if all_completed_tasks >= 10:
        all_achievements[3]['is_earned'] = True
    if all_completed_tasks >= 25:
        all_achievements[4]['is_earned'] = True
    if game_stats['streak'] >= 3:
        all_achievements[5]['is_earned'] = True
    if game_stats['streak'] >= 7:
        all_achievements[6]['is_earned'] = True
    if game_stats['points'] >= 100:
        all_achievements[7]['is_earned'] = True
    if game_stats['points'] >= 500:
        all_achievements[8]['is_earned'] = True

    earned_achievements = [a for a in all_achievements if a['is_earned']]

    return render_template(
        "dashboard.html",
        name=name,
        test_prep_completed=test_prep_completed_current,
        college_planning_completed=college_planning_completed_current,
        gpa=stats.get("gpa") or "—",
        sat_total=sat_total or "—",
        act_average=act_average or "—",
        recent_activities=recent_activities,
        activity_data=json.dumps(activity_data),
        test_date_info=test_date_info,
        earned_achievements=earned_achievements,
        game_stats=game_stats,
        suggestion=suggestion
    )


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account(user):
    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'name':
            new_name = request.form.get('name')
            db.update('users', {'name': new_name}, {'id': user.data['id']})

        elif form_type == 'email':
            new_email = request.form.get('email')
            existing_user = db.select('users', where={'email': new_email})
            if not existing_user or existing_user[0]['id'] == user.data['id']:
                db.update('users', {'email': new_email},
                          {'id': user.data['id']})
                session['user'] = new_email  # Update session

        elif form_type == 'password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if check_password_hash(user.data['password'], current_password) and new_password == confirm_password:
                hashed_password = generate_password_hash(new_password)
                db.update('users', {'password': hashed_password}, {
                          'id': user.data['id']})

        elif form_type == 'pfp':
            if 'pfp' in request.files:
                file = request.files['pfp']
                if file.filename != '':
                    # --- START: DELETE OLD PFP LOGIC (Corrected) ---
                    old_pfp_path = user.get_profile_picture()
                    if old_pfp_path:
                        # Construct the absolute path from the app's root
                        base_dir = os.path.abspath(os.path.dirname(__file__))
                        full_old_path = os.path.join(
                            base_dir, old_pfp_path.lstrip('/'))
                        if os.path.exists(full_old_path):
                            os.remove(full_old_path)
                    # --- END: DELETE OLD PFP LOGIC (Corrected) ---

                    filename = secure_filename(file.filename)
                    timestamp = int(datetime.now().timestamp())
                    unique_filename = f"{user.data['id']}_{timestamp}_{filename}"
                    filepath = os.path.join(
                        app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(filepath)

                    db_filepath = f"/{app.config['UPLOAD_FOLDER']}/{unique_filename}"
                    db.update('users', {'profile_picture': db_filepath}, {
                              'id': user.data['id']})

    user.load_user()
    return render_template('account.html', user=user, profile_picture=user.data.get('profile_picture'))


@app.route("/dashboard/test-path-builder", methods=["GET", "POST"])
@login_required
def test_path_builder(user):
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
        _generate_and_save_new_test_path(
            user.data['id'], test_path)
        return redirect(url_for("test_path_view"))
    return render_template("test_path_builder.html", **stats.get("test_path", {}))


@app.route("/dashboard/test-path-view")
@login_required
def test_path_view(user):
    return render_template("test_path_view.html")


@app.route("/dashboard/college-path-builder", methods=["GET", "POST"])
@login_required
def college_path_builder(user):
    stats = user.get_stats()
    if request.method == "POST":
        college_context = {
            'grade': request.form.get('current_grade'),
            'planning_stage': request.form.get('planning_stage'),
            'majors': request.form.get('interested_majors'),
            'target_colleges': request.form.get('target_colleges', '')
        }
        stats['college_path'] = college_context
        user.set_stats(stats)
        _generate_and_save_new_college_path(user.data['id'], college_context)
        return redirect(url_for('college_path_view'))
    return render_template("college_path_builder.html", **stats.get('college_path', {}))


@app.route('/dashboard/college-path-view')
@login_required
def college_path_view(user):
    return render_template("college_path_view.html")

# --- Stats & Tracker Routes ---


@app.route("/dashboard/stats", methods=["GET"])
@login_required
def stats(user):
    stats = user.get_stats()
    user_id = user.data['id']
    all_tasks = db.select("paths", where={"user_id": user_id})

    # --- SERVER-SIDE CALCULATION FIXES ---
    # SAT Total
    sat_ebrw = stats.get("sat_ebrw")
    sat_math = stats.get("sat_math")
    sat_total = None
    if sat_ebrw and sat_math:
        try:
            sat_total = int(sat_ebrw) + int(sat_math)
        except (ValueError, TypeError):
            sat_total = None  # Handle case where values are not valid integers

    # ACT Average
    act_scores = []
    if stats.get("act_math"):
        act_scores.append(int(stats.get("act_math")))
    if stats.get("act_reading"):
        act_scores.append(int(stats.get("act_reading")))
    if stats.get("act_science"):
        act_scores.append(int(stats.get("act_science")))

    act_average = None
    if act_scores:
        act_average = round(sum(act_scores) / len(act_scores))

    total_test_prep_completed = sum(
        1 for t in all_tasks if t['is_completed'] and t['category'] == 'Test Prep')
    total_college_planning_completed = sum(
        1 for t in all_tasks if t['is_completed'] and t['category'] == 'College Planning')

    return render_template(
        "stats.html",
        gpa=stats.get("gpa", ""),
        sat_ebrw=sat_ebrw,
        sat_math=sat_math,
        sat_total=sat_total,
        act_math=stats.get("act_math", ""),
        act_reading=stats.get("act_reading", ""),
        act_science=stats.get("act_science", ""),
        act_average=act_average,
        total_test_prep_completed=total_test_prep_completed,
        total_college_planning_completed=total_college_planning_completed
    )


@app.route("/dashboard/stats/edit", methods=["GET", "POST"])
@login_required
def edit_stats(user):
    stats = user.get_stats()
    if request.method == "POST":
        updated_stats = {
            "gpa": request.form.get("gpa", ""),
            "sat_ebrw": request.form.get("sat_ebrw", ""),
            "sat_math": request.form.get("sat_math", ""),
            "act_math": request.form.get("act_math", ""),
            "act_reading": request.form.get("act_reading", ""),
            "act_science": request.form.get("act_science", "")
        }

        for key, value in updated_stats.items():
            # Log an activity only if the value has changed
            if stats.get(key) != value and value:
                stats[key] = value
                log_activity(user.data['id'], 'stat_updated', {
                             'stat_name': key.upper(), 'stat_value': value})

        user.set_stats(stats)
        return redirect(url_for("stats"))

    return render_template(
        "edit_stats.html",
        sat_ebrw=stats.get("sat_ebrw", ""), sat_math=stats.get("sat_math", ""),
        act_math=stats.get("act_math", ""), act_reading=stats.get("act_reading", ""),
        act_science=stats.get("act_science", ""), gpa=stats.get("gpa", "")
    )


@app.route("/dashboard/tracker")
@login_required
def tracker(user):
    user_id = user.data['id']
    all_tasks = db.select(
        "paths", where={"user_id": user_id}, order_by="created_at DESC")
    test_prep_generations, college_planning_generations = {}, {}

    for task in all_tasks:
        generation_key, category = task['created_at'], task['category']
        if category == 'Test Prep':
            if generation_key not in test_prep_generations:
                test_prep_generations[generation_key] = []
            test_prep_generations[generation_key].append(task)
        elif category == 'College Planning':
            if generation_key not in college_planning_generations:
                college_planning_generations[generation_key] = []
            college_planning_generations[generation_key].append(task)

    stat_history_processed = {
        "sat_math": [], "sat_ebrw": [], "act_math": [],
        "act_reading": [], "act_science": [], "colleges_researched": [],
        "applications_submitted": [], "essay_progress": [],
        "sat_total": [], "act_composite": []
    }
    history_records = db.select(
        "stat_history", where={"user_id": user_id}, order_by="recorded_at ASC")
    for record in history_records:
        stat_name, stat_value, recorded_at = record['stat_name'], record['stat_value'], record['recorded_at']
        if stat_name in stat_history_processed:
            try:
                stat_history_processed[stat_name].append({
                    # Keep as YYYY-MM-DD for JS
                    "date": recorded_at.split(" ")[0],
                    "value": int(stat_value)
                })
            except (ValueError, TypeError):
                continue
    return render_template(
        "tracker.html",
        stat_history=stat_history_processed,
        test_prep_generations=test_prep_generations,
        college_planning_generations=college_planning_generations
    )
# --- API ROUTES ---

# ... (Previous API routes are unchanged)


@app.route('/api/test-path-status')
@login_required
def test_path_status(user):
    user_id = user.data['id']
    active_tasks = db.select(
        "paths", where={"user_id": user_id, "is_active": True, "category": "Test Prep"})
    return jsonify({"has_path": bool(active_tasks)})


@app.route('/api/college-path-status')
@login_required
def college_path_status(user):
    user_id = user.data['id']
    active_tasks = db.select(
        "paths", where={"user_id": user_id, "is_active": True, "category": "College Planning"})
    return jsonify({"has_path": bool(active_tasks)})


@app.route("/api/tasks", methods=['GET', 'POST'])
@login_required
def api_tasks(user):
    user_id = user.data['id']
    stats = user.get_stats()
    category = request.args.get('category', 'Test Prep')
    try:
        latest_task_query = """
            SELECT created_at FROM paths
            WHERE user_id=? AND category=? AND is_active=True
            ORDER BY created_at DESC LIMIT 1
        """
        latest_task_timestamp_result = db.execute(
            latest_task_query, (user_id, category))

        active_path = []
        if latest_task_timestamp_result:
            latest_timestamp = latest_task_timestamp_result[0]['created_at']
            active_path = db.select(
                "paths", where={
                    "user_id": user_id,
                    "is_active": True,
                    "category": category,
                    "created_at": latest_timestamp
                })

        if request.method == "POST" or not active_path:
            chat_record_list = db.select("chat_conversations", where={
                "user_id": user_id, "category": category})
            chat_history = json.loads(
                chat_record_list[0]['history']) if chat_record_list else []
            if category == 'College Planning':
                college_context = stats.get("college_path", {})
                tasks = _generate_and_save_new_college_path(
                    user_id, college_context, chat_history)
            else:
                test_path_info = stats.get("test_path", {})
                tasks = _generate_and_save_new_test_path(
                    user_id, test_path_info, chat_history)
            return jsonify(tasks)

        if active_path:
            active_path = sorted(active_path, key=lambda x: x['task_order'])
            tasks_with_subtasks = []
            for r in active_path:
                task_id = r['id']
                subtasks_raw = db.select(
                    "subtasks", where={"parent_task_id": task_id})
                subtasks = [{"id": s['id'], "description": s['description'],
                             "is_completed": bool(s['is_completed'])} for s in subtasks_raw]

                tasks_with_subtasks.append({
                    "id": task_id,
                    "description": r['description'],
                    "reason": r['reason'],
                    "is_completed": bool(r['is_completed']),
                    "type": r['type'],
                    "stat_to_update": r['stat_to_update'],
                    "due_date": r['due_date'],
                    "is_user_added": bool(r['is_user_added']),
                    "subtasks": subtasks
                })
            return jsonify(tasks_with_subtasks)

        return jsonify([])
    except Exception as e:
        print(f"API tasks error for category {category}: {e}")
        return jsonify({"error": "An error occurred"}), 500


@app.route("/api/update_task_status", methods=['POST'])
@login_required
def api_update_task_status(user):
    user_id = user.data['id']
    data = request.get_json()
    status = data.get("status")
    task_id = data.get("taskId")

    if status == 'complete' and task_id:
        task_info_list = db.select(
            "paths", where={"id": task_id, "user_id": user_id})
        # Check if not already completed
        if task_info_list and not task_info_list[0]['is_completed']:
            task_info = task_info_list[0]
            description = task_info['description']
            category = task_info['category']
            task_type = task_info['type']

            db.update("paths", {"is_completed": True}, where={
                      "id": task_id, "user_id": user_id})
            log_activity(user_id, 'task_completed', {
                         'description': description, 'category': category})

            # --- GAMIFICATION LOGIC ---
            points_to_add = 25 if task_type == 'milestone' else 10
            if "boss battle" in description.lower():
                points_to_add = 100

            game_stats_row = db.select(
                "gamification_stats", where={"user_id": user_id})[0]
            game_stats = {
                "points": game_stats_row['points'],
                "streak": game_stats_row['current_streak'],
                "last_date": game_stats_row['last_completed_date']
            }

            today = date.today()
            yesterday = today - timedelta(days=1)
            last_completed_date = None
            if game_stats['last_date']:
                last_completed_date = date.fromisoformat(
                    game_stats['last_date'])

            new_streak = game_stats['streak']
            if last_completed_date == today:
                # Already completed a task today, just add points
                new_streak = game_stats['streak']
            elif last_completed_date == yesterday:
                # Continuing a streak
                new_streak += 1
            else:
                # Reset streak
                new_streak = 1

            db.update("gamification_stats", {
                "points": game_stats['points'] + points_to_add,
                "current_streak": new_streak,
                "last_completed_date": today.isoformat()
            }, where={"user_id": user_id})

    return jsonify({"success": True})


@app.route("/api/chat", methods=['POST'])
@login_required
def api_chat(user):
    user_id = user.data['id']
    stats = user.get_stats()
    data = request.get_json()
    history = data.get("history", [])
    category = request.args.get('category', 'Test Prep')

    if not history or (len(history) == 1 and history[0]['role'] == 'user' and history[0]['content'] == 'INITIAL_MESSAGE'):
        history = []

    # Fetch tracker data for chat context
    stat_history = _get_stat_history_for_prompt(user_id)

    user_message = history[-1]['content'].lower() if history else ""
    if "regenerate" in user_message or "new path" in user_message or "change" in user_message:
        if category == 'College Planning':
            college_context = stats.get("college_path", {})
            new_tasks = _generate_and_save_new_college_path(
                user_id, college_context, chat_history=history)
        else:
            test_path_info = stats.get("test_path", {})
            new_tasks = _generate_and_save_new_test_path(
                user_id, test_path_info, chat_history=history)

        if history:
            history.append(
                {"role": "assistant", "content": "I've generated a new path for you based on our conversation."})

            # UPDATED LOGIC: Use upsert for simplicity and reliability
            db.upsert("chat_conversations", {
                "user_id": user_id,
                "category": category,
                "history": json.dumps(history)
            }, conflict_target=["user_id", "category"])

        return jsonify({"new_path": new_tasks})

    if category == 'College Planning':
        reply = _get_college_planning_ai_chat_response(
            history, stats, stat_history, user_id)
    else:
        reply = _get_test_prep_ai_chat_response(
            history, stats, stat_history, user_id)

    history.append({"role": "assistant", "content": reply})

    # UPDATED LOGIC: Use upsert for simplicity and reliability
    db.upsert("chat_conversations", {
        "user_id": user_id,
        "category": category,
        "history": json.dumps(history)
    }, conflict_target=["user_id", "category"])

    return jsonify({"reply": reply})


@app.route('/api/chat_history')
@login_required
def get_chat_history(user):
    user_id = user.data['id']
    category = request.args.get('category')
    chat_record_list = db.select("chat_conversations", where={
        "user_id": user_id, "category": category})
    if chat_record_list:
        history = json.loads(chat_record_list[0]['history'])
        return jsonify(history)
    return jsonify([])


@app.route('/api/reset_chat', methods=['POST'])
@login_required
def reset_chat_history(user):
    user_id = user.data['id']
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
def api_update_stats(user):
    data = request.get_json()
    stat_name = data.get("stat_name")
    stat_value = data.get("stat_value")

    if not stat_name or stat_value is None:
        return jsonify({"success": False, "error": "Missing stat name or value"}), 400

    try:
        # Always record in history
        db.insert("stat_history", {
            "user_id": user.data['id'], "stat_name": stat_name, "stat_value": stat_value
        })

        # Only update the main stats blob if it's not a temporary practice score
        if stat_name not in ["sat_total", "act_composite"]:
            stats = user.get_stats()
            stats[stat_name] = stat_value
            user.set_stats(stats)
            # LOGGING for main stats
            log_activity(user.data['id'], 'stat_updated', {
                         'stat_name': stat_name.upper(), 'stat_value': stat_value})

        return jsonify({"success": True, "message": "Stats updated successfully"})
    except Exception as e:
        print(f"Error updating stats via API: {e}")
        return jsonify({"success": False, "error": "Server error"}), 500

# --- NEW TASK & SUBTASK MANAGEMENT API ROUTES ---


@app.route('/api/add_task', methods=['POST'])
@login_required
def add_task(user):
    user_id = user.data['id']
    data = request.get_json()
    description = data.get('description')
    category = data.get('category')
    due_date = data.get('due_date')

    if not description or not category:
        return jsonify({"success": False, "error": "Description and category are required"}), 400

    # Get the highest task order for the current active path
    latest_task_query = "SELECT MAX(task_order) as max_order FROM paths WHERE user_id=? AND category=? AND is_active=True"
    max_order_result = db.execute(latest_task_query, (user_id, category))
    new_order = (max_order_result[0]['max_order'] or 0) + 1

    task_id = db.insert("paths", {
        "user_id": user_id,
        "task_order": new_order,
        "description": description,
        "is_completed": False,
        "is_active": True,
        "type": "standard",  # User-added tasks are standard by default
        "category": category,
        "due_date": due_date,
        "is_user_added": True
    })

    new_task = {
        "id": task_id, "description": description, "is_completed": False, "type": "standard",
        "stat_to_update": None, "due_date": due_date, "is_user_added": True, "subtasks": []
    }
    log_activity(user_id, 'task_added', {
                 'description': description, 'category': category})
    return jsonify({"success": True, "task": new_task})


@app.route('/api/add_subtask', methods=['POST'])
@login_required
def add_subtask(user):
    data = request.get_json()
    parent_task_id = data.get('parent_task_id')
    description = data.get('description')

    if not parent_task_id or not description:
        return jsonify({"success": False, "error": "Parent task ID and description are required"}), 400

    subtask_id = db.insert("subtasks", {
        "parent_task_id": parent_task_id,
        "description": description,
        "is_completed": False
    })
    new_subtask = {"id": subtask_id,
                   "description": description, "is_completed": False}
    return jsonify({"success": True, "subtask": new_subtask})


@app.route('/api/update_task_deadline', methods=['POST'])
@login_required
def update_task_deadline(user):
    data = request.get_json()
    task_id = data.get('taskId')
    due_date = data.get('dueDate')  # Can be a date string or None

    db.update("paths", {"due_date": due_date}, where={"id": task_id})
    return jsonify({"success": True})


@app.route('/api/update_subtask', methods=['POST'])
@login_required
def update_subtask(user):
    data = request.get_json()
    subtask_id = data.get('subtaskId')
    is_completed = data.get('is_completed')

    db.update("subtasks", {"is_completed": is_completed},
              where={"id": subtask_id})
    return jsonify({"success": True})

# --- NEW ESSAY ANALYSIS ROUTE (with more granular feedback) ---


@app.route('/api/analyze_essay', methods=['POST'])
@login_required
def analyze_essay(user):
    data = request.get_json()
    essay_text = data.get('essay_text')
    essay_prompt = data.get(
        'essay_prompt', 'a general college application essay')

    if not essay_text:
        return jsonify({"error": "Essay text is required."}), 400

    prompt = (
        f"You are an expert college admissions essay coach. Your goal is to provide constructive, actionable, and granular feedback on a student's essay. "
        f"Analyze the following essay written for the prompt: '{essay_prompt}'.\n\n"
        f"Essay Text:\n\"\"\"\n{essay_text}\n\"\"\"\n\n"
        f"Provide feedback in the following structure, using markdown for formatting. **Crucially, when you identify a strength or an area for improvement, you MUST include a short, direct quote from the essay to illustrate your point.**\n\n"
        f"### Overall Impression\n"
        f"A brief, encouraging summary of your initial thoughts on the essay.\n\n"
        f"### Strengths\n"
        f"- **Clarity and Focus:** How well does the essay address the prompt? Is there a clear central theme? (Include a quote that demonstrates this strength.)\n"
        f"- **Voice and Tone:** Does the student's personality come through? Is the tone appropriate? (Include a quote that demonstrates this strength.)\n"
        f"- **Structure and Flow:** Is the essay well-organized with a logical progression of ideas? (Include a quote that demonstrates this strength.)\n\n"
        f"### Areas for Improvement\n"
        f"- **Introduction:** Does the opening hook the reader effectively? (Include the opening sentence(s) and suggest how to make it more engaging.)\n"
        f"- **Body Paragraphs:** Is there enough specific detail, reflection, and 'show, don't tell' examples? Are there areas that could be expanded or clarified? (Include a quote that could be improved.)\n"
        f"- **Conclusion:** Does the conclusion effectively summarize the main points and leave a lasting impression? (Include the concluding sentence(s) and suggest how to make it more impactful.)\n"
        f"- **Grammar and Mechanics:** Note any recurring grammatical errors, awkward phrasing, or typos, but do not rewrite the essay. (Include a quote with an error and explain the correction.)\n\n"
        f"### Actionable Next Steps\n"
        f"1.  Provide the student with 2-3 specific, concrete steps they can take to improve their next draft.\n"
        f"2.  Keep the feedback encouraging and constructive."
    )

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return jsonify({"feedback": response.text})
    except Exception as e:
        print(f"Error in essay analysis: {e}")
        return jsonify({"error": "Failed to analyze the essay."}), 500


def _get_proactive_ai_suggestions(user):
    """Generates a proactive suggestion for the user based on their data."""
    if not os.getenv("GEMINI_API_KEY"):
        return "Welcome to Mentics! Complete some tasks to get personalized suggestions."

    user_id = user.data['id']
    stats = user.get_stats()
    onboarding_data = json.loads(
        user.data['onboarding_data']) if user.data['onboarding_data'] else {}
    stat_history = _get_stat_history_for_prompt(user_id)

    gamification_stats_list = db.select(
        "gamification_stats", where={"user_id": user_id})
    gamification_stats = gamification_stats_list[0] if gamification_stats_list else {
    }

    # Get last 5 completed tasks
    completed_tasks_raw = db.select(
        "activity_log",
        where={"user_id": user_id, "activity_type": "task_completed"},
        order_by="created_at DESC LIMIT 5"
    )
    completed_tasks = [json.loads(task['details'])['description']
                       for task in completed_tasks_raw]

    prompt = (
        f"You are an AI mentor for a high school student, acting as a supportive coach. Your task is to provide one, single, non-task-based suggestion that serves as a progress check-in, a gentle reminder, or a mental state booster. Your tone should be encouraging, insightful, and focused on the student's overall well-being and journey, not just their immediate to-do list.\n\n"
        f"Analyze the user's data to find a pattern or a key insight:\n"
        f"- Onboarding Goal: {onboarding_data.get('goal', 'Not specified')}\n"
        f"- Onboarding Anxieties: {onboarding_data.get('anxieties', 'Not specified')}\n"
        f"- Current GPA: {stats.get('gpa', 'N/A')}\n"
        f"- SAT Math: {stats.get('sat_math', 'N/A')}\n"
        f"- SAT EBRW: {stats.get('sat_ebrw', 'N/A')}\n"
        f"- ACT Composite: {stats.get('act_average', 'N/A')}\n"
        f"- Day Streak: {gamification_stats.get('current_streak', 0)}\n"
        f"- Last 5 Completed Tasks: {', '.join(completed_tasks) if completed_tasks else 'None'}\n"
        f"- Stat History:\n{stat_history}\n\n"
        f"Based on this data, provide one concise and encouraging insight. **Do not suggest a new task.** Instead, focus on motivation, strategy, and well-being. Here are some examples of the tone and style you should adopt:\n"
        f"- (If streak is high): 'A {gamification_stats.get('current_streak', 0)}-day streak is amazing! That consistency is what builds success. Keep up the great momentum.'\n"
        f"- (If a score dipped): 'I noticed your last SAT Math score was a little lower. That's a normal part of the process! It's a great opportunity to review your notes and see what you can learn from it.'\n"
        f"- (If anxieties were about time management): 'Remember when you said you were worried about time management? You've been consistently completing tasks. That shows real progress in building good habits.'\n"
        f"- (If no recent activity): 'Just checking in! Remember that even small steps forward are still steps. You've got this.'\n\n"
        f"Your response must be a single, encouraging sentence or two."
    )

    try:
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error in proactive suggestion generation: {e}")
        return "Welcome to Mentics! Let's get started on your path to success."


# --- NEW SOCIAL ROUTES ---
@app.route('/leaderboard')
@login_required
def leaderboard(user):
    # Fetch top 10 users by points
    leaderboard_data = db.execute(
        """
        SELECT u.name, g.points
        FROM gamification_stats g
        JOIN users u ON g.user_id = u.id
        ORDER BY g.points DESC
        LIMIT 10
        """
    )
    return render_template('leaderboard.html', leaderboard=leaderboard_data)


@app.route('/forum')
@app.route('/forum')
@login_required
def forum(user):
    search_query = request.args.get('search', '')

    # Base query for posts
    post_query = "SELECT * FROM forum_posts"
    params = []

    if search_query:
        post_query += " WHERE title LIKE ?"
        params.append(f"%{search_query}%")

    post_query += " ORDER BY created_at DESC"
    posts_raw = db.execute(post_query, tuple(params))
    posts = [dict(row) for row in posts_raw]

    # Fetch replies for each post
    posts_with_replies = []
    for post in posts:
        replies_raw = db.select("forum_replies", where={
                                "post_id": post['id']}, order_by="created_at ASC")
        post['replies'] = [dict(reply) for reply in replies_raw]
        posts_with_replies.append(post)

    # Fetch today's threads
    today_str = date.today().strftime('%Y-%m-%d')
    todays_threads_raw = db.execute(
        "SELECT * FROM forum_posts WHERE date(created_at) = ? ORDER BY created_at DESC", (today_str,))
    todays_threads = [dict(row) for row in todays_threads_raw]

    return render_template('forum.html',
                           posts=posts_with_replies,
                           user_name=user.get_name(),
                           todays_threads=todays_threads,
                           search_query=search_query)


@app.route('/api/posts', methods=['POST'])
@login_required
def create_post(user):
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    if title and content:
        db.insert('forum_posts', {
            'user_id': user.data['id'],
            'user_name': user.get_name(),
            'title': title,
            'content': content
        })
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Title and content are required'}), 400


@app.route('/api/replies', methods=['POST'])
@login_required
def create_reply(user):
    data = request.get_json()
    post_id = data.get('post_id')
    content = data.get('content')
    if post_id and content:
        db.insert('forum_replies', {
            'post_id': post_id,
            'user_id': user.data['id'],
            'user_name': user.get_name(),
            'content': content
        })
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Post ID and content are required'}), 400


@app.cli.command("init-db")
def init_db_command():
    """Create new tables in the database."""
    init_db()
    print("Initialized the database.")


# Determine the database path based on the environment
if 'RENDER' in os.environ:
    # On Render, use the persistent disk path provided.
    # The 'RENDER_DISK_PATH' environment variable is set in your Render dashboard.
    db_dir = os.environ.get('RENDER_DISK_PATH', '/data')
    DB_PATH = os.path.join(db_dir, 'users.db')
else:
    # For local development, use the instance folder.
    # This is a standard Flask practice and is ignored by Git.
    os.makedirs(app.instance_path, exist_ok=True)
    DB_PATH = os.path.join(app.instance_path, 'users.db')

# Initialize the database handler with the correct path
db = DatabaseHandler(DB_PATH)
# --- Auto-Create Database on Startup ---
# This block checks if the database file exists and creates it if not.
# It runs within the Flask application context to ensure all parts of the app,
# including the init_db function, are available.
with app.app_context():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. Initializing a new one...")
        try:
            init_db()
            print("Database initialized successfully.")
        except Exception as e:
            print(f"!!! CRITICAL: FAILED TO INITIALIZE DATABASE: {e}")
# --- End of Auto-Create Block ---
if __name__ == "__main__":
    app.run(debug=True)
