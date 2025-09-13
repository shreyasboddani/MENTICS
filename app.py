# app.py
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
# NEW: Import for Google OAuth
from authlib.integrations.flask_client import OAuth


# Explicitly load the .env file from the correct path
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Replace with a real secret key in production
app.url_map.strict_slashes = False
app.permanent_session_lifetime = timedelta(
    minutes=10)

# NEW: Initialize OAuth for Google Login
oauth = OAuth(app)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    client_kwargs={
        'scope': 'openid email profile'
    }
)

db = DatabaseHandler("users.db")

# ... (keep all your existing functions like init_db, helpers, decorators, AI functions, etc.)
# --- DATABASE INITIALIZATION ---


def init_db():
    db.create_table("users", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "email": "TEXT NOT NULL UNIQUE",
        "password": "TEXT NOT NULL",
        "stats": "TEXT NOT NULL"
    })
    try:
        db.add_column("users", "name", "TEXT NOT NULL DEFAULT ''")
    except:
        pass  # Column likely already exists
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
        stat_name, stat_value, recorded_at = record[2], record[3], record[4]
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
        return f(*args, **kwargs)
    return decorated_function


@app.template_filter('format_date')
def format_date_filter(s):
    if not s:
        return ""
    try:
        # UPDATED: Use the user's timezone from the session, with a fallback to UTC
        user_tz_str = session.get('timezone', 'UTC')
        user_tz = ZoneInfo(user_tz_str)

        naive_dt = datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
        utc_dt = naive_dt.replace(tzinfo=ZoneInfo("UTC"))
        user_local_dt = utc_dt.astimezone(user_tz)
        return user_local_dt.strftime('%Y-%m-%d')
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        return s.split(' ')[0] if ' ' in s else s

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


def _get_test_prep_ai_tasks(strengths, weaknesses, user_stats={}, chat_history=[], path_history={}, stat_history=""):
    """Generates test preparation tasks with a hyper-detailed prompt for maximum reliability."""

    def get_mock_tasks_reliably():
        print("--- DEBUG: Running corrected Test Prep mock generator. ---")
        all_mock_tasks = [
            {"description": "Take a full-length, timed SAT practice test.",
                "type": "milestone", "stat_to_update": "sat_total", "category": "Test Prep"},
            {"description": "Review algebra concepts from your SAT practice test.",
                "type": "standard", "stat_to_update": None, "category": "Test Prep"},
            {"description": "Practice 15 difficult vocabulary words.", "type": "standard",
                "stat_to_update": None, "category": "Test Prep"},
            {"description": "Take a timed ACT Science practice section.", "type": "milestone",
                "stat_to_update": "act_science", "category": "Test Prep"},
            {"description": "Work on time management strategies for the reading section.",
                "type": "standard", "stat_to_update": None, "category": "Test Prep"}
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

    test_date_info = "Not set by the student."
    test_date_str = user_stats.get("test_path", {}).get("test_date")
    if test_date_str:
        try:
            test_date = datetime.strptime(test_date_str, '%Y-%m-%d')
            delta = test_date - datetime.now()
            formatted_date = test_date.strftime('%B %d, %Y')
            if delta.days >= 0:
                test_date_info = f"on {formatted_date} ({delta.days} days remaining)"
            else:
                test_date_info = f"on {formatted_date} (this date has passed)"
        except ValueError:
            test_date_info = "in an invalid format."

    prompt = (
        f"# MISSION\n"
        f"You are an expert AI test prep coach ( Digital SAT & ACT). Your mission is to create a personalized, 5-step study plan that is motivating, clear, and directly addresses the student's needs. You must function as a mentor, guiding the student toward measurable progress. \n\n"
        f"# STUDENT ANALYSIS\n"
        f"Analyze the following data to understand the student's current situation:\n"
        f"- Strengths: {strengths}\n"
        f"- Weaknesses: {weaknesses}\n"
        f"- Test Date: {test_date_info}\n\n"
        f"## STUDENT PERFORMANCE & CONVERSATION HISTORY\n"
        f"This is critical context. The new plan MUST be a logical continuation of their journey.\n"
        f"- Recently Completed Tasks: {completed_tasks_str}\n"
        f"- Incomplete or Failed Tasks: {incomplete_tasks_str}\n"
        f"- Recent Conversation: {chat_history_str}\n"
        f"- Historical Performance Data (from Tracker):\n{stat_history}\n\n"
        f"# YOUR TASK: GENERATE A NEW 5-STEP PLAN\n"
        f"Based on your analysis, generate a new, 5-step study plan. The plan must be actionable and adapt to the student's recent conversation and performance. For example, if they struggled with a math concept in the chat or their tracker data shows low math scores, the new plan should include a task to address it. Aditionally, in each tasks MAKE SURE TO INCLUDE reputable resources proven to help students improve on tasks that involve studying (respective to the specific test).\n\n"
        f"# CRITICAL DIRECTIVES\n"
        f"1.  **JSON Output ONLY**: Your entire output MUST be a single, raw JSON object. Do not include any text before or after the JSON.\n"
        f"2.  **Exact Task Count**: The plan must contain EXACTLY 5 task objects in the `tasks` list.\n"
        f"3.  **Adaptive Focus**: If the conversation or tracker data indicates a clear preference for ONLY the SAT or ONLY the ACT, all 5 tasks MUST be for that specific test. Do not mix them.\n"
        f"4.  **Meaningful Milestones**: Only use the 'milestone' type for significant achievements like a full practice test or section. Use 'standard' for drills, review, or concept learning. 'stat_to_update' must be null for 'standard' tasks.\n"
        f"5.  **Correct Stat Naming**: For milestones, `stat_to_update` must be one of the following: ['sat_math', 'sat_ebrw', 'sat_total', 'act_math', 'act_reading', 'act_science', 'act_composite'].\n"
        f"6.  **Avoid Repetition**: Do not generate tasks that are identical to recently completed or incomplete tasks. The plan must feel fresh and progressive.\n\n"
        f"# JSON OUTPUT SCHEMA\n"
        f"Your output must conform strictly to this structure:\n"
        f"{{\n"
        f'  "tasks": [\n'
        f'    {{\n'
        f'      "description": "A specific, actionable, and encouraging task description.",\n'
        f'      "type": "Either \'standard\' or \'milestone\'.",\n'
        f'      "stat_to_update": "A string from the list above ONLY if type is milestone, otherwise null.",\n'
        f'      "category": "This MUST be the string \'Test Prep\'."\n'
        f'    }}\n'
        f'    // ... (four more task objects)\n'
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
        if isinstance(tasks, list) and len(tasks) > 0:
            return tasks
        raise ValueError("Invalid format from AI")
    except Exception as e:
        print(f"\n--- GEMINI API ERROR IN _get_test_prep_ai_tasks: {e} ---\n")
        return get_mock_tasks_reliably()


def _get_test_prep_ai_chat_response(history, user_stats, stat_history=""):
    if not os.getenv("GEMINI_API_KEY"):
        return "I'm in testing mode, but I'm saving our conversation!"

    test_date_info = "The student has not set a test date yet."
    test_date_str = user_stats.get("test_path", {}).get("test_date")
    if test_date_str:
        try:
            test_date = datetime.strptime(test_date_str, '%Y-%m-%d')
            delta = test_date - datetime.now()
            formatted_date = test_date.strftime('%B %d, %Y')
            if delta.days >= 0:
                test_date_info = f"The student's test is on {formatted_date} ({delta.days} from now)."
            else:
                test_date_info = f"The student's test date was {formatted_date}, which has already passed."
        except ValueError:
            test_date_info = f"The student has set a test date, but it's in an invalid format: {test_date_str}."

    system_message = (
        "You are a friendly, intelligent, and highly adaptive study coach. Your personality is encouraging and supportive. Here is the student's test date information: "
        f"'{test_date_info}'.\n\n"
        f"## Student's Historical Performance Data (from Tracker):\n{stat_history}\n\n"
        f"## Your Core Directives:\n"
        f"1.  **Initial Greeting**: If the conversation is new, greet the user warmly. Remind them of their test date if it's set and ask what they want to focus on. Mention they can say 'new path' to get an updated plan based on our chat.\n"
        f"2.  **Use Tracker Data**: If the user asks about their progress (e.g., 'how am I doing in math?'), use the historical data to give them an informed answer. Identify trends if possible.\n"
        f"3.  **Adaptive Response Length**: Your primary goal is to match the user's energy and communication style. \n"
        f"    - If the user asks a simple, direct question (e.g., 'What's next?' or 'I'm done'), provide a SHORT, concise, and encouraging answer to keep the momentum going.\n"
        f"    - If the user expresses confusion, says they are 'stuck', or asks for a detailed explanation (e.g., 'How do I solve quadratic equations?' or 'I'm having trouble with the reading section'), provide a LONGER, more detailed response. Break down the problem into clear, actionable steps, offer strategies, and be a true teacher.\n"
        f"4.  **Be a Proactive Tutor**: When a user is stuck, provide specific, actionable advice. Break down the task into smaller steps or offer alternative strategies. Do not just suggest regenerating the path unless they ask for it.\n"
        f"5.  **Acknowledge & Regenerate**: If the user asks to change focus or get a new path, confirm their request and let them know you're building a new plan for them."
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
            "type": task.get("type"), "stat_to_update": task.get("stat_to_update"),
            "category": "Test Prep", "is_active": True, "is_completed": False
        })
        new_task_data = db.select("paths", where={"id": task_id})[0]
        saved_tasks.append({
            "id": new_task_data[0], "description": new_task_data[3],
            "type": new_task_data[7], "stat_to_update": new_task_data[8],
            "is_completed": False
        })
    # LOGGING
    log_activity(user_id, 'path_generated', {'category': 'Test Prep'})
    return saved_tasks


def _get_college_planning_ai_tasks(college_context, user_stats, path_history, chat_history=[], stat_history=""):
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
        f"# MISSION\n"
        f"You are an expert AI college admissions counselor and mentor. Your mission is to generate a personalized, forward-looking 5-step roadmap that helps a high school student make measurable progress in the college planning process. Your guidance should:\n"
        f"- Push the student forward without repeating what they’ve already done.\n"
        f"- Build logically on their recent conversations, completed tasks, and current progress.\n"
        f"- Stay aligned with their grade level, planning stage, and long-term goals.\n"
        f"- Be specific, supportive, and actionable — not vague or generic.\n\n"

        f"# STUDENT ANALYSIS\n"
        f"Analyze the following data to build a deep understanding of the student:\n"
        f"- Current Grade: {college_context.get('grade', 'N/A')}\n"
        f"- Current Planning Stage: {college_context.get('planning_stage', 'N/A')}\n"
        f"- Interested Majors: {college_context.get('majors', 'N/A')}\n"
        f"- Target Colleges: {college_context.get('target_colleges', 'None specified')}\n"
        f"- Current GPA: {user_stats.get('gpa', 'N/A')}\n\n"

        f"## STUDENT PERFORMANCE & CONVERSATION HISTORY\n"
        f"This is critical context. The new plan MUST:\n"
        f"- Acknowledge their history and progress.\n"
        f"- Avoid duplicating completed or failed tasks.\n"
        f"- Create next-step tasks that extend their growth.\n\n"
        f"- Recently Completed Tasks: {completed_tasks_str}\n"
        f"- Incomplete or Failed Tasks: {incomplete_tasks_str}\n"
        f"- Recent Conversation: {chat_history_str}\n"
        f"- Historical Performance Data (from Tracker):\n{stat_history}\n\n"

        f"# YOUR TASK: GENERATE A NEW 5-STEP ROADMAP\n"
        f"Based on your analysis, generate a new, 5-step roadmap. Each task must:\n"
        f"- Be actionable and motivational.\n"
        f"- Directly support their stage-appropriate goals.\n"
        f"- Introduce fresh, concrete next steps instead of repeating old ones.\n"
        f"- Adapt in complexity and depth depending on their progress and grade.\n\n"

        f"# CRITICAL DIRECTIVES\n"
        f"1.  **JSON Output ONLY**: Your entire output MUST be a single, raw JSON object.\n"
        f"2.  **Exact Task Count**: The plan must contain EXACTLY 5 task objects.\n"
        f"3.  **Stage-Appropriate Tasks**: Align difficulty and scope to grade and planning stage. (Example: 9th graders explore interests, 12th graders finalize applications.)\n"
        f"4.  **Novelty & Continuity**: Never repeat recent tasks. Every new roadmap should clearly extend or deepen their progress.\n"
        f"5.  **Meaningful Milestones**: Use 'milestone' only for major achievements (essay draft, submitting applications, updating GPA). Use 'standard' for exploratory/research tasks. 'stat_to_update' must be null for 'standard' tasks. Never ask to update SAT in a milestone, they must update it themselves on the stats page\n"
        f"6.  **Mentorship Focus**: Don’t just assign tasks — design them as steps that build skills, confidence, and clarity about their future.\n\n"

        f"# JSON OUTPUT SCHEMA\n"
        f"Your output must conform strictly to this structure:\n"
        f"{{\n"
        f'  "tasks": [\n'
        f'    {{\n'
        f'      "description": "A specific, actionable, and encouraging task description.",\n'
        f'      "type": "Either \'standard\' or \'milestone\'.",\n'
        f'      "stat_to_update": "A string (e.g., \'gpa\', \'essay_progress\', \'applications_submitted\') ONLY if type is milestone, otherwise null.",\n'
        f'      "category": "This MUST be the string \'College Planning\'."\n'
        f'    }}\n'
        f'    // ... (four more task objects)\n'
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
        if isinstance(tasks, list) and len(tasks) > 0:
            return tasks
        raise ValueError("Invalid format from AI")
    except Exception as e:
        print(
            f"\n--- GEMINI API ERROR IN _get_college_planning_ai_tasks: {e} ---\n")
        return get_mock_tasks_reliably()


def _get_college_planning_ai_chat_response(history, user_stats, stat_history=""):
    """Generates a proactive and context-aware chat response for college planning."""
    if not os.getenv("GEMINI_API_KEY"):
        return "I'm in testing mode, but I'm saving our conversation!"

    college_info = user_stats.get("college_path", {})
    system_message = (
        "You are a friendly, intelligent, and highly adaptive college planning advisor. Your personality is encouraging, knowledgeable, and supportive. The student is in "
        f"grade {college_info.get('grade', 'N/A')} and is in the '{college_info.get('planning_stage', 'N/A')}' stage.\n\n"
        f"## Student's Historical Performance Data (from Tracker):\n{stat_history}\n\n"
        f"## Your Core Directives:\n"
        f"1.  **Initial Greeting**: If the conversation is new, greet the user warmly. Acknowledge their grade and planning stage to show you understand their context, and ask what they need help with (e.g., essays, college lists, deadlines). Mention they can say 'new path' to regenerate their plan.\n"
        f"2.  **Use Tracker Data**: If the user asks about their progress (e.g., 'how many colleges have I researched?'), use the historical data to give them an informed answer.\n"
        f"3.  **Adaptive Response Length**: Your primary goal is to match the user's communication style.\n"
        f"    - If the user gives a short update or asks a simple question (e.g., 'I finished my research' or 'What's the next step?'), provide a SHORT, concise, and encouraging response to keep them moving.\n"
        f"    - If the user expresses confusion, says they are 'stuck' on a task, or asks a broad question (e.g., 'How do I even start my college essay?' or 'I don't know what schools to look at'), provide a LONGER, more detailed and structured response. Break down the problem, offer clear steps, provide examples, and act as a knowledgeable guide.\n"
        f"4.  **Be a Proactive Advisor**: When a user is stuck, offer specific, actionable advice. Help them break the task down or find resources. Your goal is to empower them to overcome the hurdle.\n"
        f"5.  **Acknowledge & Regenerate**: If the user asks to change their plan, confirm you will regenerate it for them based on the new information they've provided."
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

        # Fetch tracker data
        stat_history = _get_stat_history_for_prompt(user_id)

        db.update("paths", {"is_active": False}, where={
                  "user_id": user_id, "category": "College Planning", "is_active": True})

        tasks = _get_college_planning_ai_tasks(
            college_context, user_stats, path_history, chat_history, stat_history)

        tasks = tasks[:5]

        if not tasks or len(tasks) != 5:
            raise ValueError(
                "AI task generation did not return the expected 5 tasks.")

        saved_tasks = []
        for i, task_data in enumerate(tasks):
            task_id = db.insert("paths", {
                "user_id": user_id, "task_order": i + 1, "description": task_data.get("description"),
                "type": task_data.get("type"), "stat_to_update": task_data.get("stat_to_update"),
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
            session["user"] = email
            session["user_id"] = user_id
            session.permanent = True
            return redirect(url_for("dashboard"))
        except Exception as e:
            print(f"Signup error: {e}")
            return render_template("signup.html", error="Email already exists!")
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
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
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

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
    user_record = db.select("users", where={"email": user_info['email']})

    if user_record:
        # User exists, log them in
        session["user"] = user_record[0][1]
        session["user_id"] = user_record[0][0]
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
        session["user"] = user_info['email']
        session["user_id"] = user_id
        session.permanent = True

    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

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
def dashboard():
    user = User.from_session(db, session)
    stats = user.get_stats()
    user_id = user.data[0]
    name = user.get_name()
    all_tasks = db.select("paths", where={"user_id": user_id})

    # --- Progress Calculations ---
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
        details = json.loads(activity[3])
        recent_activities.append({
            "type": activity[2],
            "details": details,
            "timestamp": activity[4]
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
                log[0], '%Y-%m-%d %H:%M:%S').replace(tzinfo=ZoneInfo("UTC"))
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
            days_left = (test_date - date.today()).days
            if days_left >= 0:
                test_date_info["days_left"] = days_left
                test_date_info["date_str"] = test_date.strftime('%B %d, %Y')
                if test_path_stats.get("desired_sat"):
                    test_date_info["test_type"] = "SAT"
                elif test_path_stats.get("desired_act"):
                    test_date_info["test_type"] = "ACT"
        except (ValueError, TypeError):
            pass

    # --- Achievements Logic ---
    earned_achievements = []
    all_completed_tasks = total_test_prep_completed + total_college_planning_completed

    if any(t for t in all_tasks if t[9] == 'Test Prep'):
        earned_achievements.append(
            {"icon": "🚀", "title": "Test Prep Pioneer", "description": "Generated your first Test Prep path."})
    if any(t for t in all_tasks if t[9] == 'College Planning'):
        earned_achievements.append({"icon": "🏛️", "title": "College Planner",
                                   "description": "Generated your first College Planning path."})
    if all_completed_tasks >= 1:
        earned_achievements.append(
            {"icon": "✅", "title": "First Step", "description": "Completed your first task."})
    if all_completed_tasks >= 10:
        earned_achievements.append(
            {"icon": "🔥", "title": "Task Master", "description": "Completed 10 tasks."})
    if all_completed_tasks >= 25:
        earned_achievements.append(
            {"icon": "🏆", "title": "Pathfinder Pro", "description": "Completed 25 tasks."})

    return render_template(
        "dashboard.html",
        name=name,
        test_prep_completed=test_prep_completed_current,
        total_test_prep_completed=total_test_prep_completed,
        college_planning_completed=college_planning_completed_current,
        total_college_planning_completed=total_college_planning_completed,
        gpa=stats.get("gpa") or "—",
        sat_total=sat_total or "—",
        act_average=act_average or "—",
        recent_activities=recent_activities,
        activity_data=json.dumps(activity_data),
        test_date_info=test_date_info,
        earned_achievements=earned_achievements
    )


@app.route("/dashboard/test-path-builder", methods=["GET", "POST"])
@login_required
def test_path_builder():
    user = User.from_session(db, session)
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
            user.data[0], test_path['strengths'], test_path['weaknesses'])
        return redirect(url_for("test_path_view"))
    return render_template("test_path_builder.html", **stats.get("test_path", {}))


@app.route("/dashboard/test-path-view")
@login_required
def test_path_view():
    return render_template("test_path_view.html")


@app.route("/dashboard/college-path-builder", methods=["GET", "POST"])
@login_required
def college_path_builder():
    user = User.from_session(db, session)
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
        _generate_and_save_new_college_path(user.data[0], college_context)
        return redirect(url_for('college_path_view'))
    return render_template("college_path_builder.html", **stats.get('college_path', {}))


@app.route('/dashboard/college-path-view')
@login_required
def college_path_view():
    return render_template("college_path_view.html")

# --- Stats & Tracker Routes ---


@app.route("/dashboard/stats", methods=["GET"])
@login_required
def stats():
    user = User.from_session(db, session)
    stats = user.get_stats()
    user_id = user.data[0]
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
        1 for t in all_tasks if t[4] and t[9] == 'Test Prep')
    total_college_planning_completed = sum(
        1 for t in all_tasks if t[4] and t[9] == 'College Planning')

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
def edit_stats():
    user = User.from_session(db, session)
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
                log_activity(user.data[0], 'stat_updated', {
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
def tracker():
    user = User.from_session(db, session)
    user_id = user.data[0]
    all_tasks = db.select(
        "paths", where={"user_id": user_id}, order_by="created_at DESC")
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

    stat_history_processed = {
        "sat_math": [], "sat_ebrw": [], "act_math": [],
        "act_reading": [], "act_science": [], "colleges_researched": [],
        "applications_submitted": [], "essay_progress": [],
        "sat_total": [], "act_composite": []
    }
    history_records = db.select(
        "stat_history", where={"user_id": user_id}, order_by="recorded_at ASC")
    for record in history_records:
        stat_name, stat_value, recorded_at = record[2], record[3], record[4]
        if stat_name in stat_history_processed:
            try:
                stat_history_processed[stat_name].append({
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


@app.route('/api/test-path-status')
@login_required
def test_path_status():
    user = User.from_session(db, session)
    user_id = user.data[0]
    active_tasks = db.select(
        "paths", where={"user_id": user_id, "is_active": True, "category": "Test Prep"})
    return jsonify({"has_path": bool(active_tasks)})


@app.route('/api/college-path-status')
@login_required
def college_path_status():
    user = User.from_session(db, session)
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
        latest_task_query = """
            SELECT created_at FROM paths 
            WHERE user_id=? AND category=? AND is_active=True 
            ORDER BY created_at DESC LIMIT 1
        """
        latest_task_timestamp_result = db.execute(
            latest_task_query, (user_id, category))

        active_path = []
        if latest_task_timestamp_result:
            latest_timestamp = latest_task_timestamp_result[0][0]
            active_path = db.select(
                "paths", where={
                    "user_id": user_id,
                    "is_active": True,
                    "category": category,
                    "created_at": latest_timestamp
                })

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

    if status == 'complete' and task_id:
        # Fetch task details before updating to log them
        task_info = db.select(
            "paths", where={"id": task_id, "user_id": user_id})
        if task_info:
            description = task_info[0][3]
            category = task_info[0][9]
            db.update("paths", {"is_completed": True}, where={
                      "id": task_id, "user_id": user_id})
            # LOGGING
            log_activity(user_id, 'task_completed', {
                         'description': description, 'category': category})
    return jsonify({"success": True})


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
            strengths = test_path_info.get("strengths", "general studying")
            weaknesses = test_path_info.get("weaknesses", "test-taking skills")
            new_tasks = _generate_and_save_new_test_path(
                user_id, strengths, weaknesses, chat_history=history)

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
        reply = _get_college_planning_ai_chat_response(
            history, stats, stat_history)
    else:
        reply = _get_test_prep_ai_chat_response(history, stats, stat_history)

    history.append({"role": "assistant", "content": reply})

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
    data = request.get_json()
    stat_name = data.get("stat_name")
    stat_value = data.get("stat_value")

    if not stat_name or stat_value is None:
        return jsonify({"success": False, "error": "Missing stat name or value"}), 400

    try:
        # Always record in history
        db.insert("stat_history", {
            "user_id": user.data[0], "stat_name": stat_name, "stat_value": stat_value
        })

        # Only update the main stats blob if it's not a temporary practice score
        if stat_name not in ["sat_total", "act_composite"]:
            stats = user.get_stats()
            stats[stat_name] = stat_value
            user.set_stats(stats)
            # LOGGING for main stats
            log_activity(user.data[0], 'stat_updated', {
                         'stat_name': stat_name.upper(), 'stat_value': stat_value})

        return jsonify({"success": True, "message": "Stats updated successfully"})
    except Exception as e:
        print(f"Error updating stats via API: {e}")
        return jsonify({"success": False, "error": "Server error"}), 500


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
