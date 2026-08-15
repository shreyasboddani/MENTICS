# Copyright © 2026 Mentics
# All Rights Reserved.
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from dbhelper import DatabaseHandler
from userhelper import User
from functools import wraps
import json
import hmac
import mimetypes
from google import genai
from google.genai import types
import os
import secrets
from dotenv import load_dotenv
import re
from pathlib import Path
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from authlib.integrations.flask_client import OAuth
from werkzeug.middleware.proxy_fix import ProxyFix

mimetypes.add_type('font/woff2', '.woff2')


env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
is_production = bool(os.getenv("VERCEL") or os.getenv("FLASK_ENV") == "production")
configured_secret = os.getenv("SECRET_KEY")
if is_production and not configured_secret:
    raise RuntimeError("SECRET_KEY must be configured in production.")
app.secret_key = configured_secret or secrets.token_hex(32)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=is_production,
    MAX_CONTENT_LENGTH=1024 * 1024,
)
app.url_map.strict_slashes = False
app.permanent_session_lifetime = timedelta(minutes=10)

gemini_api_key = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=gemini_api_key) if gemini_api_key else None
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
GEMINI_CHAT_MESSAGES = 12
GEMINI_CHAT_CHARACTERS = 12000
PATH_REGENERATION_CONTROL = "MENTICS_REGENERATE_PATH"


@app.after_request
def add_security_headers(response):
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'DENY')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    response.headers.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
    nonce = getattr(g, 'csp_nonce', '')
    script_sources = "'self'"
    if nonce:
        script_sources += f" 'nonce-{nonce}'"
    response.headers.setdefault(
        'Content-Security-Policy',
        "default-src 'self'; "
        f"script-src {script_sources}; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data:; connect-src 'self'; "
        "object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
    )
    if session.get('user'):
        response.headers.setdefault('Cache-Control', 'private, no-store')
    if is_production:
        response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
    return response


def _csrf_token():
    token = session.get('_csrf_token')
    if not token:
        token = secrets.token_urlsafe(32)
        session['_csrf_token'] = token
    return token


@app.before_request
def protect_state_changing_requests():
    if request.method not in {'POST', 'PUT', 'PATCH', 'DELETE'}:
        return None
    expected = session.get('_csrf_token')
    supplied = request.headers.get('X-CSRF-Token') or request.form.get('_csrf_token')
    if expected and supplied and hmac.compare_digest(expected, supplied):
        return None
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Your session expired. Refresh the page and try again.'}), 400
    return 'Invalid or expired request. Refresh the page and try again.', 400


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
        "password": "TEXT NOT NULL",  # nosec B105
        "stats": "TEXT NOT NULL",
        "name": "TEXT NOT NULL DEFAULT ''",
        "onboarding_completed": "BOOLEAN DEFAULT FALSE",
        "onboarding_data": "TEXT"
    })
    db.add_column("users", "name", "TEXT NOT NULL DEFAULT ''")
    db.add_column("users", "onboarding_completed", "BOOLEAN DEFAULT FALSE")
    db.add_column("users", "onboarding_data", "TEXT")

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
    db.add_column("paths", "task_format", "TEXT DEFAULT 'link'")
    db.add_column("paths", "is_skipped", "BOOLEAN DEFAULT FALSE")
    db.add_column("paths", "task_content_id", "INTEGER")

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
    db.create_table("activity_log", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id": "INTEGER NOT NULL",
        "activity_type": "TEXT NOT NULL",
        "details": "TEXT",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    })
    db.create_table("gamification_stats", {
        "user_id": "INTEGER PRIMARY KEY",
        "points": "INTEGER DEFAULT 0",
        "current_streak": "INTEGER DEFAULT 0",
        "last_completed_date": "TEXT",
        "FOREIGN KEY(user_id)": "REFERENCES users(id) ON DELETE CASCADE"
    })
    db.create_table("forum_posts", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id": "INTEGER NOT NULL",
        "user_name": "TEXT NOT NULL",
        "title": "TEXT NOT NULL",
        "content": "TEXT NOT NULL",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "FOREIGN KEY(user_id)": "REFERENCES users(id) ON DELETE CASCADE"
    })
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
    db.create_table("quizzes", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "task_id": "INTEGER NOT NULL",
        "title": "TEXT NOT NULL",
        "FOREIGN KEY(task_id)": "REFERENCES paths(id) ON DELETE CASCADE"
    })
    db.create_table("quiz_questions", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "quiz_id": "INTEGER NOT NULL",
        "question_text": "TEXT NOT NULL",
        "options": "TEXT NOT NULL",
        "correct_option": "INTEGER NOT NULL",
        "explanation": "TEXT",
        "FOREIGN KEY(quiz_id)": "REFERENCES quizzes(id) ON DELETE CASCADE"
    })
    db.add_column("quiz_questions", "source_or_prompt", "TEXT")

    db.create_table("quiz_results", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id": "INTEGER NOT NULL",
        "question_id": "INTEGER NOT NULL",
        "is_correct": "BOOLEAN NOT NULL",
        "submitted_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "FOREIGN KEY(user_id)": "REFERENCES users(id) ON DELETE CASCADE",
        "FOREIGN KEY(question_id)": "REFERENCES quiz_questions(id) ON DELETE CASCADE"
    })

    db.create_table("practice_sprints", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "task_id": "INTEGER NOT NULL UNIQUE",
        "title": "TEXT NOT NULL",
        "FOREIGN KEY(task_id)": "REFERENCES paths(id) ON DELETE CASCADE"
    })

    db.create_table("sprint_questions", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "sprint_id": "INTEGER NOT NULL",
        "question_text": "TEXT NOT NULL",
        "options": "TEXT NOT NULL",
        "correct_option": "INTEGER NOT NULL",
        "explanation": "TEXT",
        "FOREIGN KEY(sprint_id)": "REFERENCES practice_sprints(id) ON DELETE CASCADE"
    })

    db.create_table("sprint_results", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id": "INTEGER NOT NULL",
        "question_id": "INTEGER NOT NULL",
        "is_correct": "BOOLEAN NOT NULL",
        "submitted_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "FOREIGN KEY(user_id)": "REFERENCES users(id) ON DELETE CASCADE",
        "FOREIGN KEY(question_id)": "REFERENCES sprint_questions(id) ON DELETE CASCADE"
    })

    db.create_table("strategy_articles", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "task_id": "INTEGER NOT NULL UNIQUE",
        "title": "TEXT NOT NULL",
        "content": "TEXT NOT NULL",
        "FOREIGN KEY(task_id)": "REFERENCES paths(id) ON DELETE CASCADE"
    })

    db.add_column("paths", "secondary_content_id", "INTEGER")

    try:
        db.execute("DROP INDEX IF EXISTS idx_paths_user_category_active;")
    except Exception as e:
        print(f"Could not drop old index (this is likely fine): {e}")

    db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_paths_user_category_active_created
        ON paths (user_id, category, is_active, created_at DESC);
        """
    )
    indexes = {
        'idx_subtasks_parent': 'subtasks (parent_task_id)',
        'idx_stat_history_user_recorded': 'stat_history (user_id, recorded_at DESC)',
        'idx_activity_user_created': 'activity_log (user_id, created_at DESC)',
        'idx_quiz_results_user': 'quiz_results (user_id)',
        'idx_sprint_results_user': 'sprint_results (user_id)',
        'idx_forum_replies_post': 'forum_replies (post_id, created_at)',
    }
    for index_name, index_target in indexes.items():
        db.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {index_target}")


# --- HELPER FUNCTIONS ---


def log_activity(user_id, activity_type, details=None):
    """Helper function to log user activities into the database."""
    db.insert("activity_log", {
        "user_id": user_id,
        "activity_type": activity_type,
        "details": json.dumps(details or {})
    })


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

        readable_name = stat_name.replace('_', ' ').title()
        summary.append(
            f"- On {date}, their {readable_name} was recorded as {stat_value}.")
    return "\n".join(summary)


def _get_quiz_results_for_prompt(user_id):
    """Fetches and formats a summary of the user's recent incorrect quiz answers for AI prompts."""
    query = """
        SELECT qq.source_or_prompt, qq.question_text, qq.options, qq.correct_option, qq.explanation
        FROM quiz_results qr
        JOIN quiz_questions qq ON qr.question_id = qq.id
        WHERE qr.user_id = ? AND qr.is_correct = 0
        ORDER BY qr.submitted_at DESC
        LIMIT 5
    """
    incorrect_answers = db.execute(query, (user_id,))

    if not incorrect_answers:
        return "No recent incorrect quiz answers on record. The user may be new or performing well."

    summary = []
    for answer in incorrect_answers:
        options = json.loads(answer['options'])
        correct_answer_text = options[answer['correct_option']]
        summary.append(
            f"- Source or prompt: {answer.get('source_or_prompt') or 'Standalone question'}\n"
            f"  - Question: {answer['question_text']}\n"
            f"  - Correct Answer: \"{correct_answer_text}\"\n"
            f"  - Explanation: {answer['explanation']}"
        )
    return "\n".join(summary)


# --- DECORATORS & FILTERS ---


def _parse_db_datetime(value):
    """Parse SQLite and Neon/PostgreSQL timestamps without assuming precision."""
    if isinstance(value, datetime):
        parsed = value
    else:
        timestamp = str(value or "").strip()
        if not timestamp:
            raise ValueError("Timestamp is empty")
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=ZoneInfo("UTC"))


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        user = User.from_session(db, session)
        if user is None:
            session.clear()
            return redirect(url_for("login"))
        kwargs['user'] = user
        return f(*args, **kwargs)
    return decorated_function


@app.template_filter('format_date')
def format_date_filter(s):
    if not s:
        return ""
    try:
        user_tz_str = session.get('timezone', 'UTC')
        user_tz = ZoneInfo(user_tz_str)
        utc_dt = _parse_db_datetime(s).astimezone(ZoneInfo("UTC"))
        user_local_dt = utc_dt.astimezone(user_tz)
        return user_local_dt.strftime('%b %d, %Y')
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        return s.split(' ')[0]


@app.template_filter('time_ago')
def time_ago_filter(s):
    if not s:
        return ""
    try:
        utc_dt = _parse_db_datetime(s).astimezone(ZoneInfo("UTC"))
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


def _gemini_config(max_output_tokens, *, system_instruction=None,
                   json_output=False, thinking_level="minimal"):
    """Return a conservative generation config tuned for latency and cost."""
    config = types.GenerateContentConfig(
        max_output_tokens=max_output_tokens,
        thinking_config=types.ThinkingConfig(thinking_level=thinking_level),
        system_instruction=system_instruction,
    )
    if json_output:
        config.response_mime_type = "application/json"
    return config


def _generate_text(prompt, *, max_output_tokens=800, json_output=False,
                   thinking_level="minimal", system_instruction=None):
    """Generate validated text through the single configured Gemini model."""
    if gemini_client is None:
        raise RuntimeError("Gemini is not configured.")
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=_gemini_config(
            max_output_tokens,
            system_instruction=system_instruction,
            json_output=json_output,
            thinking_level=thinking_level,
        ),
    )
    text = (response.text or "").strip()
    if not text:
        raise ValueError("Gemini returned an empty response.")
    return text


def _compact_chat_history(history):
    """Keep recent conversational context while bounding input-token spend."""
    compact = []
    remaining_characters = GEMINI_CHAT_CHARACTERS
    for message in reversed(history[-GEMINI_CHAT_MESSAGES:]):
        content = message.get("content", "").strip()
        if not content or remaining_characters <= 0:
            continue
        content = content[-min(len(content), 2500, remaining_characters):]
        compact.append({
            "role": "model" if message.get("role") == "assistant" else "user",
            "parts": [{"text": content}],
        })
        remaining_characters -= len(content)
    compact = list(reversed(compact))

    # The interface displays a local assistant welcome before the first user
    # message. Gemini history must begin with a user and alternate roles.
    while compact and compact[0]["role"] == "model":
        compact.pop(0)
    normalized = []
    for message in compact:
        if normalized and normalized[-1]["role"] == message["role"]:
            normalized[-1]["parts"][0]["text"] += "\n\n" + message["parts"][0]["text"]
        else:
            normalized.append(message)
    while normalized and normalized[-1]["role"] == "model":
        normalized.pop()
    return normalized


def _format_chat_history_for_prompt(history):
    """Format the useful recent conversation without sending unbounded history."""
    lines = []
    for message in _compact_chat_history(history):
        role = "Assistant" if message["role"] == "model" else "User"
        lines.append(f"{role}: {message['parts'][0]['text']}")
    return "\n".join(lines) or "No conversation history yet."


def _is_path_regeneration_request(message):
    """Recognize natural requests to replace the current five-step path."""
    normalized = re.sub(r"\s+", " ", (message or "").strip().lower())
    if not normalized:
        return False

    if re.fullmatch(
        r"(?:please\s+)?(?:regen|regenerate|rebuild|refresh)(?:\s+it)?(?:\s+(?:please|pls))?[.!?]*",
        normalized,
    ):
        return True

    path_noun = r"(?:path|plan|roadmap|tasks?|steps?)"
    patterns = (
        rf"\b(?:regen|regenerate|rebuild|redo|remake|recreate|refresh|replace|refocus|tailor)\b.{{0,50}}\b{path_noun}\b",
        rf"\b{path_noun}\b.{{0,40}}\b(?:regenerated|rebuilt|redone|remade|recreated|refreshed|replaced)\b",
        rf"\b(?:change|update|revise|adjust|refocus|tailor)\b.{{0,35}}\b(?:my|the|this|these|current)?\s*{path_noun}\b",
        rf"\b(?:make|build|create|generate|give)\b.{{0,45}}\b(?:new|fresh|different|another|five[- ]step)\b.{{0,30}}\b{path_noun}\b",
        rf"\b(?:make|build|create|generate|give)\b.{{0,25}}\b(?:me\s+|my\s+|the\s+|this\s+)?{path_noun}\b.{{0,45}}\b(?:focus|focused|about|around|for|with|using|based)\b",
        rf"\b(?:new|fresh|different|another|updated|revised)\s+(?:five[- ]step\s+)?{path_noun}\b",
        rf"\b(?:make|turn)\b.{{0,20}}\b(?:my|the|this|current)\s+{path_noun}\b.{{0,35}}\b(?:focus|focused|about|centered|for)\b",
        rf"\b(?:want|need)\b.{{0,25}}\b(?:my|the|this|current)\s+{path_noun}\b.{{0,35}}\b(?:focus|focused|about|centered|changed|different)\b",
    )
    return any(re.search(pattern, normalized) for pattern in patterns)


def _generate_chat_reply(history, system_instruction):
    """Generate a concise mentor reply using only the useful recent context."""
    if gemini_client is None:
        raise RuntimeError("Gemini is not configured.")
    gemini_history = _compact_chat_history(history)
    if not gemini_history:
        last_user_message = "Hello"
        prior_history = []
    else:
        last_user_message = gemini_history[-1]["parts"][0]["text"]
        prior_history = gemini_history[:-1]

    chat = gemini_client.chats.create(
        model=GEMINI_MODEL,
        history=prior_history,
        config=_gemini_config(
            700,
            system_instruction=system_instruction,
            thinking_level="minimal",
        ),
    )
    response = chat.send_message(last_user_message)
    text = (response.text or "").strip()
    if not text:
        raise ValueError("Gemini returned an empty chat response.")
    return text


def _get_current_numbered_tasks(user_id, category):
    """Helper function to get current active tasks with numbering for a specific category."""
    active_tasks = db.select(
        "paths",
        where={
            "user_id": user_id,
            "is_active": True,
            "category": category
        },
        order_by="task_order ASC"
    )
    if not active_tasks:
        return "No active tasks at the moment."
    active_tasks = sorted(active_tasks, key=lambda x: x['task_order'])
    numbered_tasks = []
    for i, task in enumerate(active_tasks, 1):
        status = "✅ (Completed)" if task['is_completed'] else "⏳ (In Progress)"
        numbered_tasks.append(f"Task {i}: {task['description']} - {status}")
    return "\n".join(numbered_tasks)


def _complete_five_step_plan(tasks, category):
    """Guarantee five usable tasks when an AI response is incomplete."""
    defaults = {
        "Test Prep": [
            {"task_format": "link", "description": "Review one weak skill with an official SAT or ACT lesson and write down three takeaways.", "reason": "A focused review gives the rest of this path a clear foundation.", "type": "standard", "stat_to_update": None, "category": "Test Prep", "difficulty": "easy"},
            {"task_format": "link", "description": "Complete a timed set of ten official practice questions in your weakest section.", "reason": "A short timed set reveals the exact mistakes worth fixing next.", "type": "standard", "stat_to_update": None, "category": "Test Prep", "difficulty": "medium"},
            {"task_format": "review", "description": "Build an error log for every missed question and label each mistake by concept, process, or timing.", "reason": "An error log turns practice results into a repeatable improvement system.", "type": "standard", "stat_to_update": None, "category": "Test Prep", "difficulty": "medium"},
            {"task_format": "link", "description": "Redo the missed questions without notes and explain the correct method in your own words.", "reason": "Retrieval and explanation confirm that the correction will stick.", "type": "standard", "stat_to_update": None, "category": "Test Prep", "difficulty": "medium"},
            {"task_format": "link", "description": "Boss Battle: Take a timed official practice module and record your updated score.", "reason": "A timed checkpoint measures whether this cycle improved accuracy and pacing.", "type": "milestone", "stat_to_update": None, "category": "Test Prep", "difficulty": "hard"},
        ],
        "College Planning": [
            {"description": "Define your three non-negotiables for college fit and rank them in order.", "reason": "Clear criteria keep your college search focused on schools that genuinely fit you.", "type": "standard", "stat_to_update": None, "category": "College Planning", "difficulty": "easy"},
            {"description": "Research five colleges against your fit criteria and save one concrete note about each.", "reason": "Evidence-based research creates a balanced, intentional school list.", "type": "standard", "stat_to_update": None, "category": "College Planning", "difficulty": "medium"},
            {"description": "Create a deadline tracker for applications, financial aid, testing, and recommendations.", "reason": "One source of truth reduces missed deadlines and application stress.", "type": "standard", "stat_to_update": None, "category": "College Planning", "difficulty": "easy"},
            {"description": "Draft a one-page activities inventory with impact, scope, and time commitment for each activity.", "reason": "A strong inventory makes future application writing faster and more specific.", "type": "standard", "stat_to_update": None, "category": "College Planning", "difficulty": "medium"},
            {"description": "Write a first personal-statement outline built around one specific experience and what changed because of it.", "reason": "A focused narrative foundation prevents a generic personal statement.", "type": "milestone", "stat_to_update": None, "category": "College Planning", "difficulty": "hard"},
        ],
    }
    normalized = []
    seen = set()
    for task in tasks or []:
        if not isinstance(task, dict) or not task.get("description"):
            continue
        description_key = task["description"].strip().lower()
        if not description_key or description_key in seen:
            continue
        normalized.append(task)
        seen.add(description_key)
        if len(normalized) == 5:
            break
    for fallback in defaults[category]:
        if len(normalized) == 5:
            break
        if fallback["description"].lower() not in seen:
            normalized.append(dict(fallback))
    return normalized[:5]


def _get_sprint_results_for_prompt(user_id):
    """Fetches and formats a summary of the user's recent incorrect sprint answers for AI prompts."""
    query = """
        SELECT sq.question_text, sq.options, sq.correct_option, sq.explanation
        FROM sprint_results sr
        JOIN sprint_questions sq ON sr.question_id = sq.id
        WHERE sr.user_id = ? AND sr.is_correct = 0
        ORDER BY sr.submitted_at DESC
        LIMIT 5
    """
    incorrect_answers = db.execute(query, (user_id,))
    if not incorrect_answers:
        return "No recent incorrect answers in practice sprints."

    summary = []
    for answer in incorrect_answers:
        options = json.loads(answer['options'])
        correct_answer_text = options[answer['correct_option']]
        summary.append(
            f"- Question: {answer['question_text']}\n"
            f"  - Correct Answer: \"{correct_answer_text}\"\n"
            f"  - Explanation: {answer['explanation']}"
        )
    return "\n".join(summary)


def _derive_skill_name(description, weakness_hint=""):
    text = (description or "").strip()
    if not text:
        text = (weakness_hint or "target skill").strip()
    cleaned = re.sub(r"^(Practice Sprint|Sprint|Quiz|Review|Strategy|Task)\s*[:\-]\s*", "", text, flags=re.I)
    cleaned = re.sub(r"\b(?:for|on|about)\b.*$", "", cleaned, flags=re.I)
    cleaned = cleaned.strip(" -:;.")
    if not cleaned:
        cleaned = (weakness_hint or "target skill").strip()
    return cleaned[:120] or "target skill"


def build_strategy_article(skill, weakness_note, task_description=""):
    """Create a task-specific teaching guide that prepares a student to solve the sprint or quiz confidently."""
    skill_name = (task_description or skill or "your target skill").strip() or "your target skill"
    if skill and skill_name == "your target skill":
        skill_name = skill
    title = f"Strategies for {skill_name}"
    weakness_text = (weakness_note or "This skill needs a systematic approach, not memorization.").strip()
    focus_line = skill_name if skill_name and skill_name.lower() != "your target skill" else "this skill"

    content = f"""# {title}

## Why this matters
This sprint is built around {focus_line}. The goal is not to memorize a random trick. It is to recognize the pattern, choose the right approach, and then verify the answer before moving on.

A lot of mistakes happen when students rush the setup, skip the check step, or confuse a concept with a similar-looking idea. If you slow down just enough to identify the pattern, this topic becomes much more predictable.

> Focus point: {weakness_text}

## Step 1: Identify the structure before solving
Read the prompt in chunks and ask: What is the problem really asking for? Are there clues that show a special rule, formula, relationship, or reasoning pattern?

For {focus_line}, the fastest route is to avoid solving immediately and instead classify the task:
- Is this a pattern question, a relationship question, a system question, or a word/grammar rule?
- Can the problem be solved by rewriting the information, plugging in values, comparing choices, or identifying a trap?
- Is there a hidden constraint such as a sign change, unit issue, or a restriction like "positive" or "integer"?

If you can name the structure, the next step is much easier.

## Step 2: Use a repeatable method
Do not invent a new approach every time. Use one reliable routine:
1. Rewrite the information in simpler form.
2. Identify the key rule or relationship.
3. Solve in the most direct way possible.
4. Check whether the result fits the original question.

This routine matters because most mistakes are process mistakes, not concept mistakes. Students often skip the check step or change the model halfway through.

## Step 3: Watch for common traps
### Common traps
- Treating a phrase or symbol as a literal match when the real structure is different.
- Ignoring a restriction such as "positive," "integer," or "greater than zero."
- Solving a step correctly but forgetting to return to the original question.
- Overreading the wording and picking a more complicated method than necessary.
- Making sign, fraction, variable, or wording mistakes in the middle of the process.

When you see an answer that looks too easy or too complicated, pause and ask whether it matches the exact wording of the question.

## Step 4: Build a quick decision checklist
Before you answer, ask yourself:
- Did I identify the actual type of problem?
- Did I use the correct rule or relationship?
- Did I eliminate the obvious trap?
- Does my answer fit the context and units?
- Can I explain my choice in one sentence?

If you can answer those questions, you are usually ready to move on.

## Worked example
Use this pattern on a sample question built around {focus_line}:

"A student is asked to solve a problem involving {focus_line}. The correct approach is to recognize the relationship, rewrite the information clearly, and solve with the shortest reliable method."

Here is the process:
1. Read the prompt and underline the exact task.
2. Name the mathematical or reasoning pattern.
3. Translate the information into a simple form.
4. Solve using one clean method.
5. Check the result against the original conditions.

The key skill is not speed; it is precision. A shorter, more controlled method is usually more reliable than a dramatic one.

## Quick self-check before the sprint or quiz
Before you submit an answer, do this checklist:
- I know what type of problem this is.
- I have identified the correct rule or relationship.
- I have written down the necessary setup clearly.
- I have checked whether the answer is reasonable.
- I can explain the logic without reading the steps off a formula sheet.

If you can do that, you are ready for the sprint or quiz.

## Final takeaway
The best way to improve {focus_line} is to repeat the same process on every question:
- identify the structure
- choose the right method
- check the result
- eliminate common traps

That habit turns a hard topic into a readable pattern. Once you practice it consistently, the quiz and sprint will feel much more manageable because you are not guessing—you are applying a repeatable strategy.
"""
    return {"title": title, "content": content}


def _get_path_progress_context(user_id, category):
    """Summarize how far the user has progressed in the active path so regeneration can build from the right place."""
    tasks = db.select(
        "paths",
        where={"user_id": user_id, "category": category},
        order_by="task_order ASC"
    )
    if not tasks:
        return "The student has no previous path yet, so generate a fresh five-step path."

    completed = [task for task in tasks if task.get("is_completed")]
    skipped = [task for task in tasks if task.get("is_skipped")]
    incomplete = [task for task in tasks if not task.get("is_completed")]

    if not incomplete:
        return (
            f"The student completed the entire prior {category} path "
            f"({len(completed)} tasks). Build a logical continuation rather than repeating the same steps."
        )

    next_task_order = min(task["task_order"] for task in incomplete)
    next_task = next((task for task in tasks if task["task_order"] == next_task_order), None)
    next_desc = next_task.get("description", "the next path step") if next_task else "the next path step"
    return (
        f"The student has completed {len(completed)} out of {len(tasks)} tasks in this {category} path, "
        f"with {len(skipped)} skipped steps. The next uncompleted item is task {next_task_order}: '{next_desc}'. "
        "Build the next five-step path as a continuation from this point, not a duplicate of the previous plan."
    )


def _get_test_prep_ai_tasks(strengths, weaknesses, test_focus, current_scores=None, desired_scores=None, test_date_str=None, hours_per_week=None, chat_history=None, path_history=None, stat_history="", quiz_results="", sprint_results="", path_progress_context=""):
    """Generates hyper-intelligent, adaptive test prep tasks, now including interactive Practice Sprints, Strategy Articles, and better context."""

    current_scores = current_scores or {}
    desired_scores = desired_scores or {}
    chat_history = chat_history or []
    path_history = path_history or {}

    def get_mock_tasks_reliably():
        """A fallback function to provide tasks if the AI service is unavailable."""
        print("--- DEBUG: Running fallback mock task generator for Test Prep. ---")

        return [
            {"task_format": "link", "description": "Take a full-length, timed SAT practice test from the [official College Board site](https://satsuite.collegeboard.org/sat/practice-preparation/practice-tests).",
             "reason": "This is a 'boss battle' to test your skills under pressure.", "type": "milestone", "stat_to_update": "sat_total", "category": "Test Prep", "difficulty": "hard"},
            {"task_format": "link", "description": "Review algebra concepts using [Khan Academy](https://www.khanacademy.org/math/algebra).",
             "reason": "A strong algebra foundation is crucial.", "type": "standard", "stat_to_update": None, "category": "Test Prep", "difficulty": "medium"},
            {"task_format": "link", "description": "Practice time management for the reading section.", "reason": "Pacing is key to finishing on time.",
                "type": "standard", "stat_to_update": None, "category": "Test Prep", "difficulty": "medium"}
        ]

    if not os.getenv("GEMINI_API_KEY"):
        return get_mock_tasks_reliably()

    completed_tasks_str = "\n".join(
        [f"- {task['description']}" for task in path_history.get('completed', [])]) or "None."
    incomplete_tasks_str = "\n".join(
        [f"- {task['description']}" for task in path_history.get('incomplete', [])]) or "None."
    latest_user_message = next((msg['content'] for msg in reversed(
        chat_history) if msg['role'] == 'user'), "N/A")
    chat_history_str = _format_chat_history_for_prompt(chat_history)

    # --- Test Date Formatting ---
    test_date_info = "Not set."
    if test_date_str:
        try:
            user_tz = ZoneInfo(session.get('timezone', 'UTC'))
            test_date = datetime.strptime(test_date_str, '%Y-%m-%d').date()
            delta = test_date - datetime.now(user_tz).date()
            formatted_date = test_date.strftime('%B %d, %Y')
            if delta.days >= 0:
                test_date_info = f"on {formatted_date} ({delta.days} days remaining)"
            else:
                test_date_info = f"on {formatted_date} (this date has passed)"
        except (ValueError, ZoneInfoNotFoundError):
            test_date_info = "Invalid date format."

    # --- Format Current Scores for Prompt ---
    current_scores_formatted = []
    if current_scores.get("current_sat_ebrw"):
        current_scores_formatted.append(
            f"SAT EBRW: {current_scores['current_sat_ebrw']}")
    if current_scores.get("current_sat_math"):
        current_scores_formatted.append(
            f"SAT Math: {current_scores['current_sat_math']}")
    if current_scores.get("current_act_composite"):
        current_scores_formatted.append(
            f"ACT Composite: {current_scores['current_act_composite']}")
    if current_scores.get("current_act_math"):
        current_scores_formatted.append(
            f"ACT Math: {current_scores['current_act_math']}")
    if current_scores.get("current_act_reading"):
        current_scores_formatted.append(
            f"ACT Reading: {current_scores['current_act_reading']}")
    if current_scores.get("current_act_science"):
        current_scores_formatted.append(
            f"ACT Science: {current_scores['current_act_science']}")
    current_scores_str = ", ".join(
        current_scores_formatted) if current_scores_formatted else "Not provided"

    # --- Format Desired Scores for Prompt ---
    desired_scores_formatted = []
    if desired_scores.get("desired_sat"):
        desired_scores_formatted.append(
            f"SAT: {desired_scores['desired_sat']}")
    if desired_scores.get("desired_act"):
        desired_scores_formatted.append(
            f"ACT: {desired_scores['desired_act']}")
    desired_scores_str = ", ".join(
        desired_scores_formatted) if desired_scores_formatted else "Not specified"

    # --- Determine Test Focus Description ---
    focus_desc = "SAT"
    if test_focus == 'act':
        focus_desc = "ACT"
    elif test_focus == 'both':
        focus_desc = "both SAT and ACT"

    prompt = (
        f"# MISSION\n"
        f"You are an elite AI test prep coach for Mentics. Your mission is to generate an intelligent, 5-step study plan tailored to the student's evolving needs, demonstrating a deep understanding of their history and context SPECIFICALY FOR THE DIGITAL SAT AND THE ACT.\n\n"

        f"## CRITICAL SCENARIO ANALYSIS\n"
        f"1.  **Regeneration Request:** This generation was initiated from the student's path conversation. Treat the student's most recent substantive path request as an explicit override: every task must directly reflect its requested focus, constraints, timing, or changed goal. If the final message is only a short follow-up such as 'why?' or 'do it,' resolve it against the preceding user messages instead of using the short follow-up as the plan focus.\n"
        f"2.  **Post-Path Continuation:** If the student just completed all tasks, the new plan MUST be a logical next step (e.g., analyzing scores, planning long-term improvements).\n"
        f"3.  **Standard Generation:** Otherwise, generate a standard path that builds on their history.\n\n"

        f"# STUDENT ANALYSIS DATA\n"
        f"- **Primary Test Focus:** {focus_desc}\n"
        f"- Strengths: {strengths}\n"
        f"- Weaknesses: {weaknesses} <== **Base your tasks primarily on these specific weaknesses.**\n"
        f"- **Current Scores (Baseline):** {current_scores_str}\n"
        f"- Desired Scores: {desired_scores_str}\n"
        f"- Official Test Date: {test_date_info}\n"

        f"- Estimated Weekly Study Time: {hours_per_week or 'Not specified'} hours\n\n"

        f"## HISTORICAL & CONVERSATIONAL CONTEXT\n"
        f"- **Most Recent User Request (highest priority):** '{latest_user_message}'\n"
        f"- **Recent Conversation:**\n{chat_history_str}\n"
        f"- **Path Progress Context:** {path_progress_context or 'Not provided.'}\n"
        f"- Recently Completed Tasks: {completed_tasks_str}\n"
        f"- Incomplete Tasks from Previous Path: {incomplete_tasks_str}\n"
        f"- Historical Performance Data (Tracker):\n{stat_history}\n\n"

        f"## RECENT QUIZ PERFORMANCE (Incorrect Answers)\n"
        f"This shows specific questions the user recently got wrong on CUMULATIVE quizzes. Use this granular data to create targeted follow-up tasks.\n{quiz_results}\n\n"

        f"## RECENT PRACTICE SPRINT PERFORMANCE (Incorrect Answers)\n"
        f"This shows specific questions the user recently got wrong on FOCUSED sprints. This is the most important data for identifying specific skill gaps.\n{sprint_results}\n\n"

        f"# YOUR TASK: GENERATE EXACTLY 5 NEW STEPS (for {focus_desc.upper()})\n"
        f"- Return exactly five unique tasks. Do not repeat an old task unless the student's latest request clearly requires it.\n"
        f"- **Focus on {focus_desc.upper()}:** All content, examples, and resources MUST be relevant to the chosen test format(s).\n"
        f"- **Task Format Logic (Crucial!):** You must differentiate between passive learning and active practice. \n"
        f"  - If a task involves **actively solving problems or answering questions or mastering a math concept or advancing/consolidating knowlege **, it MUST be a `practice_sprint`.\n"
        f"  - If a task involves **reading articles, or watching content on yt or using external resources**, it MUST be a `link`, `strategy`, or `review` task.\n"
        f"- **Synthesize, Don't Just List:** Your primary function is to connect multiple data points to create hyper-specific tasks. Generic tasks like 'Practice Algebra' are forbidden.\n"
        f"- **Extreme Specificity & Actionable Verbs:** Descriptions must be granular and start with a strong verb (e.g., 'Master', 'Analyze', 'Implement').\n"
        f"- **Incorporate Multiple Formats:** The plan must include a mix of task types, including at least one `practice_sprint`.\n"
        f"- ** DIGITAL SAT & ACT FOCUS:** All tasks must be relevant to the unique formats and content of the Digital SAT and ACT, do not include thigns that were on the Paper SAT like ELA IS NOW JS EBRW AND MATH ACT IS similar to paper.\n"
        f"- **Data-Driven Justification:** The `reason` for each task is critical. It MUST explicitly reference the student's personal data (e.g., 'This is important because you listed Geometry as a weakness...').\n\n"
        f"- **Math:** is the user is struggling in math the biggest thing to ensure is they know how to use desmos regression for the tricky constant questions. table regressiopn, tilde regression, and system of eqs regression and also normalizing the x values. This is like a starting point for math but get specific with other topics if they need specific practice.\n\n"

        f"## `practice_sprint` & `strategy_article` GENERATION (CRITICAL)\n"
        f"This format is ONLY for tasks that require the user to practice questions. When you create a `practice_sprint`, you MUST ALSO generate a corresponding `strategy_article`.\n"
        f"1.  **Hyper-Focused Sprint:** The `sprint_content` must contain exactly 5 SAT-level questions targeting a single, narrow skill (e.g., 'verb tense consistency' or 'solving systems of linear equations'). This skill must be chosen based on the student's weaknesses or incorrect answers.\n"
        f"2.  **Actionable Strategy Article:** The `strategy_article` must be a high-quality, concise guide (using Markdown) that teaches the student how to master the specific skill in the sprint.\n\n"

        f"## `quiz` GENERATION DIRECTIVES (CRITICAL)\n"
        f"A `quiz` is different from a sprint and has the task type `quiz`. It is a CUMULATIVE review of a broader topic and should be used to test overall knowledge, not for focused practice.\n"
        f"1.  **Strategic Placement:** A quiz should ideally follow a 'Resource Task' (`link`).\n"
        f"2.  **Complete Source or Prompt:** Every quiz question MUST include `source_or_prompt`. Put the full passage, excerpt, equation, data set, scenario, or chart/diagram description the question depends on in this field. Never refer to a passage, table, graph, or text that is not included. For a standalone problem, put its complete setup in `source_or_prompt`, then use `question_text` only for the question being asked. Include a source name and markdown link when adapting attributed material; otherwise identify it as an original Mentics practice prompt.\n"
        f"3.  **SAT-Level Comprehensiveness:** Questions must mirror official SAT complexity, including complete reading passages, 'words in context', and multi-step math problems.\n"
        f"4.  **Targeted Content:** The quiz topic MUST address one of the student's listed weaknesses.\n"
        f"5.  **Detailed Explanations:** Every question must have an explanation.\n"
        f"6.  Each quiz should have 5-10 questions.\n\n"

        f"# CRITICAL DIRECTIVES & JSON SCHEMA\n"
        f"1.  **JSON Output ONLY**: Your output MUST be a single, raw JSON object.\n"
        f"2.  **Task Formats**: You must use a mix of `link`, `quiz`, `practice_sprint`, `strategy`, and `review` based on the logic in 'YOUR TASK'.\n"
        f"3.  **Data-Driven Justification**: The `reason` field is mandatory and must explain *why* the task is assigned, referencing the student's data.\n"
        f"4.  **Milestones & 'Boss Battles'**: Use 'milestone' for major assessments. 'Boss Battle' descriptions must start with 'Boss Battle:' they DO NOT have any practice sprints with them and they DO NOT habve a guide they SHOULD direct the user to take a test on one prep or bluebook.\n"
        f"5.  **Correct Stat Naming**: `stat_to_update` must be one of: ['sat_math', 'sat_ebrw', 'sat_total', 'act_math', 'act_reading', 'act_science', 'act_composite'].\n\n"
        f"6.  ** The tasks without any practice sprints should tell user to read or watch something and then summarize key strategies. The tasks with practice sprints should have a strategy article that teaches the skill being practiced. The quiz tasks should be cumulative and test a broader topic, not just one skill.\n\n"

        f"# JSON OUTPUT STRUCTURE\n"
        f"{{\n"
        f'  "tasks": [\n'
        f'    {{\n'
        f'      "task_format": "Can be \'link\', \'quiz\', \'strategy\', \'review\', or \'practice_sprint\'.",\n'
        f'      "description": "Hyper-specific instruction. For a sprint, describe the skill (e.g., \'Practice Sprint: Subject-Verb Agreement\'). MUST include markdown link if format is \'link\'.",\n'
        f'      "reason": "Mandatory, data-driven justification referencing the student\'s specific stats, weaknesses, or history.",\n'
        f'      "type": "Either \'standard\' or \'milestone\'.",\n'
        f'      "stat_to_update": "Valid stat name ONLY if type is milestone, otherwise null.",\n'
        f'      "category": "This MUST be the string \'Test Prep\'.",\n'
        f'      "difficulty": "Either \'easy\', \'medium\', \'hard\', or \'epic\'.",\n'
        f'      "quiz_content": {{  // For \'quiz\' format ONLY. 5-10 questions. \n'
        f'          "title": "Title of the quiz",\n'
        f'          "questions": [ {{"source_or_prompt": "Complete passage, problem setup, data, or attributed source with link", "question_text": "Question asked about the source or prompt", "options": [], "correct_option": 0, "explanation": "..."}} ]\n'
        f'      }},\n'
        f'      "sprint_content": {{  // REQUIRED if task_format is \'practice_sprint\', otherwise null.\n'
        f'          "title": "Title of the sprint (e.g., \'Algebra: Functions Practice\')",\n'
        f'          "questions": [ {{"question_text": "...", "options": [], "correct_option": 0, "explanation": "..."}} ] // EXACTLY 5 questions on ONE skill\n'
        f'      }},\n'
        f'      "strategy_article": {{ // REQUIRED if task_format is \'practice_sprint\', otherwise null.\n'
        f'          "title": "Article Title (e.g., \'Strategies for Tackling Function Questions\')",\n'
        f'          "content": "Full article text in Markdown format. Explain key concepts and provide 2-3 actionable strategies."\n'
        f'      }}\n'
        f'    }}\n'
        f'  ]\n'
        f'}}'
    )
    try:
        raw_text = _generate_text(
            prompt,
            max_output_tokens=6000,
            json_output=True,
            thinking_level="low",
        )

        response_data = None

        import re
        cleaned_text = re.sub(
            r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', raw_text)

        try:

            response_data = json.loads(cleaned_text)
        except json.JSONDecodeError as direct_e:

            print(
                f"--- Direct JSON parsing failed: {direct_e}. Attempting extraction... ---")
            match = re.search(
                r'^\s*(\{.*\}|\[.*\])\s*$', cleaned_text, re.DOTALL)
            if match:
                json_candidate = match.group(1)
                try:
                    response_data = json.loads(json_candidate)
                    print("--- Successfully parsed extracted JSON. ---")
                except json.JSONDecodeError as extract_e:

                    raise ValueError(
                        f"Failed to parse cleaned AI JSON response even after extraction: {extract_e}\nCleaned text (first 2000 chars): {cleaned_text[:2000]}") from extract_e
            else:

                raise ValueError(
                    f"No valid JSON structure found in the cleaned AI response.\nCleaned text (first 2000 chars): {cleaned_text[:2000]}") from direct_e

        tasks = response_data.get("tasks", [])

        def looks_like_practice(desc):
            if not desc:
                return False
            kws = ['practice', 'solve', 'questions', 'problem', 'drill',
                   'master', 'consolidate', 'attempt', 'answer', 'worksheet', 'sprint']
            desc_l = desc.lower()
            return any(k in desc_l for k in kws)

        def make_mock_sprint(skill):
            questions = [{'question_text': f"SAT/ACT practice {qi+1} on {skill}.", 'options': ['A', 'B',
                                                                                               'C', 'D'], 'correct_option': 0, 'explanation': f"Key steps for {skill}."} for qi in range(5)]
            return {'title': f"Practice Sprint: {skill}", 'questions': questions}

        def make_strategy_article(skill, weakness_note, task_description=""):
            return build_strategy_article(skill, weakness_note, task_description)

        def make_mock_quiz(topic):
            questions = [{
                'source_or_prompt': (
                    f"Original Mentics practice prompt on {topic}: use the information "
                    f"provided in this complete setup for item {qi + 1}."
                ),
                'question_text': f"Which option correctly answers practice item {qi + 1} on {topic}?",
                'options': ['A', 'B', 'C', 'D'],
                'correct_option': 0,
                'explanation': f"Solution for {topic}.",
            } for qi in range(7)]
            return {'title': f"Cumulative Quiz: {topic}", 'questions': questions}

        normalized = []

        for t in tasks if isinstance(tasks, list) else []:
            try:

                if not isinstance(t, dict):
                    continue
                desc = t.get('description', '') or ''
                t['category'] = 'Test Prep'
                inferred_format = t.get('task_format') or (
                    'practice_sprint' if looks_like_practice(desc) else 'link')
                t['task_format'] = inferred_format

                skip_practice = False
                if t['task_format'] in ('link', 'strategy', 'review'):
                    if len(desc) < 40 and t['task_format'] == 'link':
                        main_weak = (weaknesses.split(',')[0].strip(
                        ) if weaknesses else '') or 'your weakest subskill'
                        t['description'] = desc.strip(
                        ) + f" Read/watch content on {main_weak} & summarize 3 key strategies."
                    if t['task_format'] in ('strategy', 'review'):
                        skip_practice = True
                        topic = (weaknesses.split(',')[0].strip() if weaknesses else '') or desc.split(
                            ' on ')[-1].split('.')[0][:40].strip() or 'strategies'
                        article = t.get('strategy_article')
                        task_skill = _derive_skill_name(desc, topic)
                        if not article or not article.get('content') or len(article.get('content', '')) < 1200:
                            t['strategy_article'] = make_strategy_article(
                                task_skill, t.get('reason') or f"Focus on {topic}.", desc)
                        t.pop('sprint_content', None)

                if (not skip_practice) and (t['task_format'] == 'practice_sprint' or looks_like_practice(desc)):
                    t['task_format'] = 'practice_sprint'
                    skill = _derive_skill_name(desc, weaknesses)
                    if not t.get('sprint_content'):
                        t['sprint_content'] = make_mock_sprint(skill)
                    article = t.get('strategy_article')
                    if not article or not article.get('content') or len(article.get('content', '')) < 1200:
                        t['strategy_article'] = make_strategy_article(
                            skill, t.get('reason') or f"Target {skill}.", desc)

                desc_l = desc.lower()
                if t.get('task_format') == 'quiz' or any(k in desc_l for k in ('quiz', 'cumulative')):
                    t['task_format'] = 'quiz'
                    quiz_topic = (weaknesses.split(',')[0].strip() if weaknesses else '') or desc.split(
                        ' on ')[-1].split('.')[0][:40].strip() or 'mixed topics'
                    if not t.get('quiz_content'):
                        t['quiz_content'] = make_mock_quiz(quiz_topic)
                    quiz_questions = t['quiz_content'].get('questions', [])
                    for question in quiz_questions:
                        if not isinstance(question, dict):
                            continue
                        source_or_prompt = next((
                            question.get(key) for key in (
                                'source_or_prompt', 'source', 'prompt', 'passage', 'context'
                            ) if isinstance(question.get(key), str) and question.get(key).strip()
                        ), None)
                        question['source_or_prompt'] = source_or_prompt or (
                            "Original Mentics standalone practice prompt. All required "
                            "information is included in the question below."
                        )

                if 'boss battle' in desc.lower() or desc.startswith('Boss Battle'):
                    t['type'] = 'milestone'
                    preferred_test = 'SAT' if test_focus != 'act' else 'ACT'
                    stat_map = {'SAT': 'sat_total', 'ACT': 'act_composite'}
                    t['stat_to_update'] = stat_map.get(preferred_test)
                    resource_hint = f'Take a full-length, timed official {preferred_test} practice test (e.g., College Board Bluebook for SAT, official ACT platform).'
                    cb_link = 'https://satsuite.collegeboard.org/sat/practice-preparation/practice-tests' if preferred_test == 'SAT' else ''
                    act_link = 'https://www.act.org/content/act/en/products-and-services/the-act/test-preparation/free-act-test-prep.html' if preferred_test == 'ACT' else ''  # Example ACT link
                    link_md = f" [Official Practice]({cb_link or act_link})" if (
                        cb_link or act_link) else ""
                    norm_desc = f"Boss Battle: {resource_hint}{link_md}"
                    if not desc.startswith('Boss Battle:'):
                        t['description'] = norm_desc
                    elif resource_hint.lower() not in desc.lower():
                        t['description'] = desc.strip() + ' ' + \
                            resource_hint + link_md

                if t.get('type') == 'milestone':
                    valid_stats = ['sat_math', 'sat_ebrw', 'sat_total',
                                   'act_math', 'act_reading', 'act_science', 'act_composite']
                    if t.get('stat_to_update') not in valid_stats:
                        t['stat_to_update'] = None
                normalized.append(t)
            except Exception as norm_e:
                print(
                    f"--- Error normalizing task: {norm_e} --- Task data: {t}")
                continue

        if isinstance(normalized, list) and len(normalized) > 0:
            return normalized
        elif isinstance(normalized, list) and len(normalized) == 0 and tasks:
            print("--- WARNING: Normalization removed all tasks. Falling back. ---")
            return get_mock_tasks_reliably()
        else:
            raise ValueError(
                "AI response did not contain a valid 'tasks' list or normalization produced no tasks")

    except Exception as e:

        print(
            f"\n--- GEMINI API OR PROCESSING ERROR IN _get_test_prep_ai_tasks: {e} ---\n")

        if 'raw_text' not in locals():
            raw_text = "Raw text extraction failed."
        print(
            f"--- Raw Response (if available, first 500 chars): {str(raw_text)[:500]} ---")
        return get_mock_tasks_reliably()


def _has_incomplete_earlier_task(user_id, task):
    return bool(db.execute_for_one(
        """SELECT id FROM paths
           WHERE user_id=? AND category=? AND is_active=True
             AND task_order<? AND is_completed=False LIMIT 1""",
        (user_id, task['category'], task['task_order'])
    ))


@app.route('/strategy_article/<int:task_id>')
@login_required
def strategy_article(user, task_id):

    task = db.select_one(
        "paths", where={"id": task_id, "user_id": user.data['id'], "is_active": True})
    if not task:
        return "Article not found or you do not have permission to view it.", 404
    if _has_incomplete_earlier_task(user.data['id'], task):
        return "Complete the earlier path step before opening this strategy guide.", 403

    article = db.select_one("strategy_articles", where={"task_id": task_id})
    if not article:
        return "Article not found for this task.", 404

    return render_react("article", {
        "name": user.get_name(),
        "article": dict(article),
    }, f"{article.get('title', 'Strategy')} | Mentics")


@app.route('/api/practice_sprint/<int:task_id>')
@login_required
def get_practice_sprint(user, task_id):
    task_info = db.select_one(
        "paths", where={"id": task_id, "user_id": user.data['id'], "is_active": True})
    if not task_info or task_info['task_format'] != 'practice_sprint':
        return jsonify({"error": "Practice sprint not found"}), 404
    if _has_incomplete_earlier_task(user.data['id'], task_info):
        return jsonify({"error": "Complete the earlier path step first."}), 409

    sprint_details = db.select_one(
        "practice_sprints", where={"task_id": task_id})
    if not sprint_details:
        return jsonify({"error": "Sprint details not found"}), 404

    questions_raw = db.select("sprint_questions", where={
                              "sprint_id": sprint_details['id']})
    questions = [{
        "id": q['id'],
        "question_text": q['question_text'],
        "options": json.loads(q['options'])
    } for q in questions_raw]

    return jsonify({"title": sprint_details['title'], "questions": questions})


@app.route('/api/submit_sprint_results', methods=['POST'])
@login_required
def submit_sprint_results(user):
    data = request.get_json(silent=True) or {}
    try:
        score = _score_assessment_results(user.data['id'], data.get('results'), 'sprint')
        return jsonify(score)
    except ValueError as error:
        return jsonify({"success": False, "error": str(error)}), 400


def _score_assessment_results(user_id, submitted, kind):
    if not isinstance(submitted, list) or not 1 <= len(submitted) <= 50:
        raise ValueError("Submit between 1 and 50 answers.")
    if kind == 'quiz':
        query = """SELECT qq.id, qq.correct_option, qq.options, qq.explanation,
                          p.id AS task_id, p.category, p.task_order
                   FROM quiz_questions qq
                   JOIN quizzes q ON q.id=qq.quiz_id
                   JOIN paths p ON p.id=q.task_id
                   WHERE qq.id=? AND p.user_id=? AND p.is_active=True"""
        result_table = 'quiz_results'
    else:
        query = """SELECT sq.id, sq.correct_option, sq.options, sq.explanation,
                          p.id AS task_id, p.category, p.task_order
                   FROM sprint_questions sq
                   JOIN practice_sprints ps ON ps.id=sq.sprint_id
                   JOIN paths p ON p.id=ps.task_id
                   WHERE sq.id=? AND p.user_id=? AND p.is_active=True"""
        result_table = 'sprint_results'
    scored = []
    seen = set()
    checked_tasks = set()
    for answer in submitted:
        if not isinstance(answer, dict):
            raise ValueError("Each answer must be an object.")
        try:
            question_id = int(answer.get('question_id'))
            selected_option = int(answer.get('selected_option'))
        except (TypeError, ValueError) as error:
            raise ValueError("Each answer needs a valid question and option.") from error
        if question_id in seen:
            raise ValueError("A question can only be submitted once.")
        seen.add(question_id)
        question = db.execute_for_one(query, (question_id, user_id))
        if not question:
            raise ValueError("One or more questions do not belong to this account.")
        if question['task_id'] not in checked_tasks:
            if _has_incomplete_earlier_task(user_id, question):
                raise ValueError("Complete the earlier path step first.")
            checked_tasks.add(question['task_id'])
        options = json.loads(question['options'])
        if not 0 <= selected_option < len(options):
            raise ValueError("One or more selected options are invalid.")
        is_correct = selected_option == int(question['correct_option'])
        db.insert(result_table, {
            'user_id': user_id, 'question_id': question_id, 'is_correct': is_correct
        })
        scored.append({
            'question_id': question_id, 'is_correct': is_correct,
            'correct_option': int(question['correct_option']),
            'explanation': question.get('explanation') or '',
        })
    return {
        'success': True, 'correct': sum(1 for row in scored if row['is_correct']),
        'total': len(scored), 'results': scored,
    }


def _generate_and_save_new_test_path(user_id, test_path_info, chat_history=None):
    chat_history = chat_history or []
    user_record = db.select_one("users", where={"id": user_id})
    user_stats = json.loads(user_record['stats']) if user_record else {
    }

    strengths = test_path_info.get("strengths", "")
    weaknesses = test_path_info.get("weaknesses", "")

    test_focus = test_path_info.get("test_focus", "sat")
    test_date_str = test_path_info.get("test_date")
    hours_per_week = test_path_info.get("hours_per_week")

    current_scores = {
        "current_sat_ebrw": test_path_info.get("current_sat_ebrw"),
        "current_sat_math": test_path_info.get("current_sat_math"),
        "current_act_composite": test_path_info.get("current_act_composite"),
        "current_act_math": test_path_info.get("current_act_math"),
        "current_act_reading": test_path_info.get("current_act_reading"),
        "current_act_science": test_path_info.get("current_act_science"),
    }
    desired_scores = {
        "desired_sat": test_path_info.get("desired_sat"),
        "desired_act": test_path_info.get("desired_act"),
    }

    all_tasks = db.select(
        "paths", where={"user_id": user_id, "category": "Test Prep"})
    path_history = {
        "completed": [t for t in all_tasks if t['is_completed']],
        "incomplete": [t for t in all_tasks if not t['is_completed']]
    }

    stat_history = _get_stat_history_for_prompt(user_id)
    quiz_results = _get_quiz_results_for_prompt(user_id)
    sprint_results = _get_sprint_results_for_prompt(user_id)

    path_progress_context = _get_path_progress_context(user_id, "Test Prep")
    tasks = _get_test_prep_ai_tasks(
        strengths=strengths,
        weaknesses=weaknesses,
        test_focus=test_focus,
        current_scores=current_scores,
        desired_scores=desired_scores,
        test_date_str=test_date_str,
        hours_per_week=hours_per_week,
        chat_history=chat_history,
        path_history=path_history,
        stat_history=stat_history,
        quiz_results=quiz_results,
        sprint_results=sprint_results,
        path_progress_context=path_progress_context,
    )

    tasks = _complete_five_step_plan(tasks, "Test Prep")
    if len(tasks) != 5:
        raise ValueError("Path generation must produce exactly five usable tasks.")

    saved_tasks = []
    with db.transaction() as transaction:
        transaction.update("paths", {"is_active": False}, where={
            "user_id": user_id, "category": "Test Prep", "is_active": True
        })
        for i, task in enumerate(tasks):
            task_format = task.get("task_format", "link")
            task_data = {
                "user_id": user_id, "task_order": i + 1,
                "description": task.get("description"), "reason": task.get("reason"),
                "type": task.get("type"), "stat_to_update": task.get("stat_to_update"),
                "category": "Test Prep", "is_active": True,
                "is_completed": False, "task_format": task_format,
            }
            task_id = transaction.insert("paths", task_data)

            if task_format == 'quiz' and task.get('quiz_content'):
                quiz_id = transaction.insert("quizzes", {
                    "task_id": task_id,
                    "title": task['quiz_content'].get("title", "Quiz"),
                })
                for question in task['quiz_content'].get("questions", []):
                    transaction.insert("quiz_questions", {
                        "quiz_id": quiz_id,
                        "source_or_prompt": question.get("source_or_prompt"),
                        "question_text": question.get("question_text"),
                        "options": json.dumps(question.get("options")),
                        "correct_option": question.get("correct_option"),
                        "explanation": question.get("explanation"),
                    })
                transaction.update("paths", {"task_content_id": quiz_id}, where={"id": task_id})

            elif task_format == 'practice_sprint' and task.get('sprint_content') and task.get('strategy_article'):
                sprint_id = transaction.insert("practice_sprints", {
                    "task_id": task_id,
                    "title": task['sprint_content'].get("title", "Practice Sprint"),
                })
                for question in task['sprint_content'].get("questions", []):
                    transaction.insert("sprint_questions", {
                        "sprint_id": sprint_id,
                        "question_text": question.get("question_text"),
                        "options": json.dumps(question.get("options")),
                        "correct_option": question.get("correct_option"),
                        "explanation": question.get("explanation"),
                    })
                article_id = transaction.insert("strategy_articles", {
                    "task_id": task_id,
                    "title": task['strategy_article'].get("title"),
                    "content": task['strategy_article'].get("content"),
                })
                transaction.update("paths", {
                    "task_content_id": sprint_id,
                    "secondary_content_id": article_id,
                }, where={"id": task_id})

            saved_tasks.append({**task_data, "id": task_id})

        transaction.insert("activity_log", {
            "user_id": user_id,
            "activity_type": "path_generated",
            "details": json.dumps({"category": "Test Prep"}),
        })
    return saved_tasks


def _get_test_prep_ai_chat_response(history, user_stats, stat_history="", quiz_results="", sprint_results="", user_id=None):
    if not os.getenv("GEMINI_API_KEY"):
        return "I'm in testing mode, but I'm saving our conversation!"

    test_path_info = user_stats.get("test_path", {})
    test_focus = test_path_info.get("test_focus", "not specified")
    desired_sat = test_path_info.get("desired_sat", "N/A")
    desired_act = test_path_info.get("desired_act", "N/A")
    current_sat_ebrw = test_path_info.get("current_sat_ebrw", "N/A")
    current_sat_math = test_path_info.get("current_sat_math", "N/A")
    current_act_comp = test_path_info.get(
        "current_act_composite", "N/A")
    hours_per_week = test_path_info.get("hours_per_week", "N/A")
    strengths = test_path_info.get("strengths", "Not provided")
    weaknesses = test_path_info.get("weaknesses", "Not provided")

    test_date_info = "The student has not set a test date yet."
    test_date_str = test_path_info.get("test_date")

    if test_date_str:
        try:
            user_tz_str = session.get('timezone', 'UTC')
            try:
                user_tz = ZoneInfo(user_tz_str)
            except ZoneInfoNotFoundError:
                user_tz = ZoneInfo("UTC")
            test_date = datetime.strptime(
                test_date_str, '%Y-%m-%d').date()  # Use .date()

            delta = test_date - datetime.now(user_tz).date()
            formatted_date = test_date.strftime('%B %d, %Y')
            if delta.days >= 0:
                test_date_info = f"The student's test is on {formatted_date} ({delta.days} days from now)."
            else:
                test_date_info = f"The student's test date was {formatted_date}, which has already passed."
        except ValueError:
            test_date_info = f"The student has set a test date, but it's in an invalid format: {test_date_str}."

    current_tasks = "No tasks available." if user_id is None else _get_current_numbered_tasks(
        user_id, "Test Prep")

    focus_desc = "SAT"
    if test_focus == 'act':
        focus_desc = "ACT"
    elif test_focus == 'both':
        focus_desc = "both SAT and ACT"
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

        f"## CURRENT STUDENT ANALYSIS (CONTEXT FOR YOUR RESPONSE)\n"
        f"This is the specific student you are currently coaching:\n"
        f"- **Primary Test Focus:** {focus_desc}\n"

        f"- Current SAT EBRW: {current_sat_ebrw}, Current SAT Math: {current_sat_math}\n"

        f"- Current ACT Composite: {current_act_comp}\n"

        f"- Desired SAT: {desired_sat}, Desired ACT: {desired_act}\n"
        f"- Strengths: {strengths}\n"
        f"- Weaknesses: {weaknesses}\n"
        f"- Official Test Date Info: {test_date_info}\n"
        f"- Estimated Weekly Study Time: {hours_per_week} hours\n"
        f"- Historical Performance Data (from Tracker): {stat_history}\n"
        f"- Current Active Tasks (numbered):\n{current_tasks}\n\n"
        f"## RECENT QUIZ PERFORMANCE (Incorrect Answers)\n{quiz_results}\n\n"

        f"## RECENT SPRINT PERFORMANCE (Incorrect Answers)\n{sprint_results}\n\n"
        f"This shows specific questions the user recently got wrong. Use this granular data to mentor them in their path."

        "## CORE COACHING DIRECTIVES (Your Rules of Engagement)\n"
        "0.  **Initial Greeting**: Your first reply must be a warm, concise welcome. Mention once that the student can ask naturally to regenerate, replace, or refocus their path and include the focus they want.\n"
        "1.  **Primary Goal: Path & App Support**: Your main purpose is to help the user with their current, active Path. Answer their questions about specific tasks, why they were assigned, and how to approach them. You must also be able to answer general questions about using the Mentics application's features as described above.\n"
        f"2.  **Path Regeneration Protocol**: If the student asks to regen, regenerate, replace, rebuild, redo, refocus, or create a path—even in casual language or as a follow-up to an earlier request—respond with exactly `{PATH_REGENERATION_CONTROL}` and nothing else. Mentics will use that private control response to perform the update. Never say you lack access to the backend, dashboard, path, or app. If the student is only exploring an idea and has not asked to change the path, coach them normally.\n"
        "3.  **Provide High-Quality Resources**: When a student is stuck or asks for help, provide specific, reputable, and free resources using markdown links (e.g., `[Khan Academy](https://...)`, official practice test PDFs, specific educational YouTube videos).\n"
        "4.  **Actionable Focus**: Every response must provide a clear next step, a useful tip, or actionable guidance. Never leave the user wondering what to do next.\n"
        "5.  **Adaptive Response Length**: \n"
        "    - For quick questions, provide short, concise answers KEEP THESE UNDER 100 WORDS).\n"
        "    - For complex requests (e.g., explaining a difficult concept), provide detailed, step-by-step explanations using lists or bullet points KEEP THESE UNDER 250 words.\n"
        "6.  **Proactive and Strategic Guidance**: Offer actionable strategies, study tips, and relevant resources when a user expresses difficulty. Address their weaknesses directly but leverage their strengths to build confidence.\n"
        "7.  **Mentorship Tone**: Always maintain a supportive, motivating, and realistic tone. Your goal is to empower the student and encourage consistent effort and progress."
    )

    try:
        return _generate_chat_reply(history, system_message)
    except Exception as e:
        print(
            f"\n--- GEMINI API ERROR IN _get_test_prep_ai_chat_response: {e} ---\n")
        return "Sorry, I encountered an error connecting to the AI."


def _get_college_planning_ai_tasks(college_context, user_stats, path_history, chat_history=None, stat_history=""):
    """Generates hyper-intelligent, adaptive college planning tasks with a detailed, gamified prompt."""

    chat_history = chat_history or []

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
        return all_mock_tasks

    if not os.getenv("GEMINI_API_KEY"):
        return get_mock_tasks_reliably()

    completed_tasks_str = "\n".join(
        [f"- {task['description']}" for task in path_history.get('completed', [])]) or "None."
    incomplete_tasks_str = "\n".join(
        [f"- {task['description']}" for task in path_history.get('incomplete', [])]) or "None."
    chat_history_str = _format_chat_history_for_prompt(chat_history)
    latest_user_message = next((msg['content'] for msg in reversed(
        chat_history) if msg['role'] == 'user'), "N/A")

    prompt = (
        f"# MISSION\n"
        f"You are an expert AI college admissions counselor for the Mentics platform. Your mission is to generate an intelligent, 5-step roadmap that provides a clear, logical, and motivating path for a high school student. The plan must be a thoughtful continuation of their journey, not just a random list of tasks.\n\n"

        f"## CRITICAL SCENARIO ANALYSIS (ACTION REQUIRED)\n"
        f"First, determine the student's current situation and choose your generation strategy:\n"
        f"1.  **Regeneration Request:** This generation was initiated from the student's path conversation. Treat the student's most recent substantive path request as an explicit override: every task must directly reflect its requested focus, constraints, deadlines, or changed goal. If the final message is only a short follow-up such as 'why?' or 'do it,' resolve it against the preceding user messages instead of using the short follow-up as the plan focus.\n"
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

        f"# YOUR TASK: GENERATE EXACTLY 5 NEW STEPS\n"
        f"- Return exactly five unique tasks. Do not repeat an old task unless the student's latest request clearly requires it.\n"
        f"- **Synthesize, Don't Just List:** Your primary function is to connect the student's grade, goals, and history to create hyper-specific tasks. Generic tasks like 'Work on your essay' are forbidden.\n"
        f"- **Extreme Specificity & Actionable Verbs:** Descriptions must be granular and start with a strong verb (e.g., 'Draft', 'Research', 'Finalize'). Instead of 'Explore majors', generate 'Research the core curriculum for a Computer Science major at {college_context.get('target_colleges', 'one of your target schools')} to see if it aligns with your interests.'\n"
        f"- **Incorporate Multiple Formats:** The plan must include a mix of task types. Include at least one **Resource Task** (e.g., 'Watch this guide on financial aid'), one **Action Task** (e.g., 'Draft your Common App activity list'), and one **Strategic/Review Task** (e.g., 'Analyze the supplemental essay prompts for your target schools and categorize them by theme').\n"
        f"- **Data-Driven Justification:** The `reason` for each task is critical. It MUST explicitly reference the student's personal data (grade, major, goals). For example: 'As an 11th grader interested in Biology, it is crucial to start identifying teachers for your recommendation letters now.'\n\n"

        f"# CRITICAL DIRECTIVES & JSON SCHEMA\n"
        f"1.  **JSON Output ONLY**: Your entire output MUST be a single, raw JSON object. No extra text.\n"
        f"2.  **New Task Formats**: You can now use `strategy` and `review` in the `task_format` field for tasks focused on planning or self-evaluation. These do not require a markdown link.\n"
        f"3.  **Data-Driven Justification**: The `reason` field is mandatory and must explain *why* this task is relevant to *this specific student* by referencing their data (e.g., '...because you're in 12th grade and application deadlines are approaching').\n"
        f"4.  **Meaningful Milestones & 'Boss Battles'**: Use 'milestone' for significant achievements (e.g., completing an essay draft, submitting an application). A 'Boss Battle' description must begin with 'Boss Battle:'.\n"
        f"5.  **Refer to Test Prep Path**: If test prep is relevant, do not create a task for it. Instead, create a task that instructs the user to work on their 'Test Prep Path' within the Mentics app.\n\n"

        f"# JSON OUTPUT STRUCTURE\n"
        f"{{\n"
        f'  "tasks": [\n'
        f'    {{\n'
        f'      "task_format": "Either \'link\', \'strategy\', or \'review\'.",\n'
        f'      "description": "Hyper-specific instruction. MUST include a markdown link if format is \'link\'.",\n'
        f'      "reason": "Mandatory, data-driven justification referencing the student\'s specific grade, goals, or history.",\n'
        f'      "type": "Either \'standard\' or \'milestone\'.",\n'
        f'      "stat_to_update": "A string (\'gpa\', \'essay_progress\', \'applications_submitted\') ONLY if type is milestone, otherwise null.",\n'
        f'      "category": "This MUST be the string \'College Planning\'.",\n'
        f'      "difficulty": "Either \'easy\', \'medium\', \'hard\', or \'epic\'."\n'
        f'    }}\n'
        f'  ]\n'
        f'}}'
    )
    try:
        response_text = _generate_text(
            prompt,
            max_output_tokens=2500,
            json_output=True,
            thinking_level="low",
        )
        response_data = json.loads(response_text)
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

    current_tasks = "No tasks available." if user_id is None else _get_current_numbered_tasks(
        user_id, "College Planning")

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


        "## CORE COACHING DIRECTIVES (Your Rules of Engagement)\n"
        "0.  **Initial Greeting**: Your first reply must be a warm, concise welcome. Mention once that the student can ask naturally to regenerate, replace, or refocus their path and include the focus they want.\n"
        "1.  **Primary Goal: Path & App Support**: Your main purpose is to help the user with their current, active Path. Answer their questions about specific tasks, why they were assigned, and how to approach them. You must also be able to answer general questions about using the Mentics application's features as described above.\n"
        f"2.  **Path Regeneration Protocol**: If the student asks to regen, regenerate, replace, rebuild, redo, refocus, or create a path—even in casual language or as a follow-up to an earlier request—respond with exactly `{PATH_REGENERATION_CONTROL}` and nothing else. Mentics will use that private control response to perform the update. Never say you lack access to the backend, dashboard, path, or app. If the student is only exploring an idea and has not asked to change the path, coach them normally.\n"
        "3.  **Provide High-Quality Resources**: When a student is stuck or needs guidance, provide specific, reputable, and free resources using markdown links (e.g., links to the Common App, financial aid websites like FAFSA, or helpful articles on essay writing).\n"
        "4.  **Actionable Guidance**: Every response must give the student a clear next step, a valuable resource, or a concrete action to take. Never leave the user wondering what to do next.\n"
        "5.  **Adaptive Response Length**:\n"
        "    - For simple questions, provide short, concise answers KEEP THESE UNDER 100 WORDS.\n"
        "    - For complex requests (e.g., essay brainstorming, advice on choosing colleges), provide detailed, structured responses using lists or bullet points KEEP THESE UNDER 250 WORDS.\n"
        "6.  **Proactive Advising**: If the student seems stuck on a task like 'write an essay', break it down into smaller, actionable steps (e.g., 'Let's start by brainstorming three key experiences you could write about.').\n"
        "7.  **Mentorship Tone**: Always maintain a supportive, encouraging, and realistic tone to keep the student motivated throughout the often-stressful college application process.\n"
        "8. **Suggest Test Prep Path When Relevant**: If the student mentions standardized tests (SAT/ACT) or seems uncertain about test preparation, proactively suggest they explore the MENTICS Test Prep path for tailored study plans and resources.\n"
    )

    try:
        return _generate_chat_reply(history, system_message)
    except Exception as e:
        print(
            f"\n--- GEMINI API ERROR IN _get_college_planning_ai_chat_response: {e} ---\n")
        return "Sorry, I encountered an error connecting to the AI."


def _generate_and_save_new_college_path(user_id, college_context, chat_history=None):
    """Gathers all context, generates, and saves a new college planning path."""
    chat_history = chat_history or []
    user_record = db.select_one("users", where={"id": user_id})
    if not user_record:
        raise ValueError(f"User with ID {user_id} not found.")
    user_stats = json.loads(user_record['stats'])

    all_college_tasks = db.select(
        "paths", where={"user_id": user_id, "category": "College Planning"})
    path_history = {
        "completed": [task for task in all_college_tasks if task['is_completed']],
        "incomplete": [task for task in all_college_tasks if not task['is_completed']],
    }
    stat_history = _get_stat_history_for_prompt(user_id)
    tasks = _complete_five_step_plan(
        _get_college_planning_ai_tasks(
            college_context, user_stats, path_history, chat_history, stat_history
        ),
        "College Planning",
    )
    if len(tasks) != 5:
        raise ValueError("Path generation must produce exactly five usable tasks.")

    saved_tasks = []
    with db.transaction() as transaction:
        transaction.update("paths", {"is_active": False}, where={
            "user_id": user_id,
            "category": "College Planning",
            "is_active": True,
        })
        for index, task in enumerate(tasks):
            path_data = {
                "user_id": user_id,
                "task_order": index + 1,
                "description": task.get("description"),
                "reason": task.get("reason"),
                "type": task.get("type"),
                "stat_to_update": task.get("stat_to_update"),
                "category": "College Planning",
                "is_active": True,
                "is_completed": False,
                "task_format": task.get("task_format", "link"),
            }
            task_id = transaction.insert("paths", path_data)
            saved_tasks.append({**task, **path_data, "id": task_id})

        transaction.insert("activity_log", {
            "user_id": user_id,
            "activity_type": "path_generated",
            "details": json.dumps({"category": "College Planning"}),
        })
    return saved_tasks


@app.route("/dashboard/tracker")
@login_required
def tracker(user):
    user_id = user.data['id']

    # --- 1. Comprehensive Stat History Processing ---
    stat_history_raw = db.select(
        "stat_history", where={"user_id": user_id}, order_by="recorded_at ASC")

    history_by_stat = {}
    for record in stat_history_raw:
        stat_name = record['stat_name']
        if stat_name not in history_by_stat:
            history_by_stat[stat_name] = []
        try:
            history_by_stat[stat_name].append({
                "date": record['recorded_at'].split(" ")[0],
                "value": float(record['stat_value'])
            })
        except (ValueError, TypeError):
            continue  # Skip records with non-numeric values

    # --- 2. Calculate Composite/Total Scores from Sectional History ---
    sat_scores_by_date = {}
    for entry in history_by_stat.get('sat_math', []):
        sat_scores_by_date.setdefault(entry['date'], {})[
            'math'] = entry['value']
    for entry in history_by_stat.get('sat_ebrw', []):
        sat_scores_by_date.setdefault(entry['date'], {})[
            'ebrw'] = entry['value']

    sat_total_history = history_by_stat.get('sat_total', [])
    for date, scores in sat_scores_by_date.items():
        if 'math' in scores and 'ebrw' in scores:
            total = scores['math'] + scores['ebrw']

            if not any(entry['date'] == date for entry in sat_total_history):
                sat_total_history.append({"date": date, "value": total})

    if 'sat_total' in history_by_stat:
        history_by_stat['sat_total'] = sorted(
            sat_total_history, key=lambda x: x['date'])

    act_scores_by_date = {}
    for subject in ['act_math', 'act_reading', 'act_science']:
        for entry in history_by_stat.get(subject, []):
            act_scores_by_date.setdefault(
                entry['date'], []).append(entry['value'])

    act_composite_history = history_by_stat.get('act_composite', [])
    for date, scores in act_scores_by_date.items():
        if scores:

            composite = round(sum(scores) / len(scores))

            if not any(entry['date'] == date for entry in act_composite_history):
                act_composite_history.append(
                    {"date": date, "value": composite})

    if 'act_composite' in history_by_stat:
        history_by_stat['act_composite'] = sorted(
            act_composite_history, key=lambda x: x['date'])

    # --- 3. KPI Calculation (Most recent, best, improvement) ---
    kpis = {}
    stat_names_for_kpi = [
        "sat_total", "sat_math", "sat_ebrw",
        "act_composite", "act_math", "act_reading", "act_science",
        "gpa", "colleges_researched", "applications_submitted"
    ]
    for name in stat_names_for_kpi:
        records = history_by_stat.get(name)
        if records and len(records) > 0:
            values = [r['value'] for r in records]
            kpis[name] = {
                'latest': values[-1],
                'best': max(values),
                'improvement': values[-1] - values[0] if len(values) > 1 else 0
            }

    # --- 4. Path History Processing (Separated by Category) ---
    all_tasks_raw = db.select(
        "paths", where={"user_id": user_id}, order_by="created_at DESC")

    test_prep_generations, college_planning_generations = {}, {}

    for task in all_tasks_raw:
        gen_key, category = task['created_at'], task['category']
        target_dict = test_prep_generations if category == 'Test Prep' else college_planning_generations

        if gen_key not in target_dict:
            target_dict[gen_key] = {'date': gen_key,
                                    'category': category, 'tasks': []}
        target_dict[gen_key]['tasks'].append(task)

    test_prep_history = sorted(
        test_prep_generations.values(), key=lambda x: x['date'], reverse=True)
    for gen in test_prep_history:
        gen['tasks'].sort(key=lambda x: x['task_order'])

    college_planning_history = sorted(
        college_planning_generations.values(), key=lambda x: x['date'], reverse=True)
    for gen in college_planning_history:
        gen['tasks'].sort(key=lambda x: x['task_order'])

    return render_react("tracker", {
        "name": user.get_name(),
        "statHistory": history_by_stat,
        "kpis": kpis,
        "testPrepHistory": test_prep_history,
        "collegePlanningHistory": college_planning_history,
    }, "Tracker | Mentics")


def _get_tracker_ai_analysis(user):
    """Generates a comprehensive AI-powered analysis of all user progress."""
    user_id = user.data['id']
    stats = user.get_stats()

    # --- Gather All Data Points ---
    stat_history_summary = _get_stat_history_for_prompt(user_id)
    quiz_results_summary = _get_quiz_results_for_prompt(user_id)

    all_paths_raw = db.select(
        "paths", where={"user_id": user_id}, order_by="created_at DESC")
    path_history_summary = []
    if all_paths_raw:
        completed_count = sum(1 for p in all_paths_raw if p['is_completed'])
        total_count = len(all_paths_raw)
        path_history_summary.append(
            f"Overall Task Completion: {completed_count}/{total_count} tasks completed.")

        last_path_date = all_paths_raw[0]['created_at'].split(' ')[0]
        last_path_category = all_paths_raw[0]['category']
        path_history_summary.append(
            f"Most Recent Path: A '{last_path_category}' path generated on {last_path_date}.")

    prompt = (
        f"You are an expert education analyst. Produce a concise markdown report for the student.\n\n"
        f"CONTEXT:\n- Recent score history (latest 20 records):\n{stat_history_summary}\n\n"
        f"- Recent incorrect quiz examples (up to 5):\n{quiz_results_summary}\n\n"
        f"- Path/task summary:\n{_get_current_numbered_tasks(user_id, 'Test Prep')}\n{_get_current_numbered_tasks(user_id, 'College Planning')}\n{', '.join(path_history_summary)}\n\n"
        f"INSTRUCTIONS:\n1) Provide a 3-sentence overall progress snapshot.\n2) List 3 specific strengths with data references.\n3) List 3 specific weaknesses or patterns to address, referencing quiz examples when useful.\n4) Provide 3 prioritized, actionable next steps (short, doable, and measurable).\n5) Suggest one micro-quiz/task the student can do in the next 48 hours.\n6) Keep tone encouraging and avoid technical jargon.\n\n"
    )

    if os.getenv("GEMINI_API_KEY"):
        try:
            return _generate_text(prompt, max_output_tokens=1000)
        except Exception as e:
            print(f"Error in tracker AI analysis (remote): {e}")

    try:

        analysis_lines = []

        latest_scores = stat_history_summary.splitlines()[:6]
        analysis_lines.append("### 📈 Progress Snapshot")
        if latest_scores:
            analysis_lines.append("""
Recent notable entries:
""")
            analysis_lines.extend([f"- {s}" for s in latest_scores])
        else:
            analysis_lines.append("No recent score records available.")

        analysis_lines.append("\n### 🏆 Key Strengths")
        if 'improved' in stat_history_summary.lower() or 'increase' in stat_history_summary.lower():
            analysis_lines.append(
                "- Detected improvement trend in at least one metric based on recent records.")
        else:
            analysis_lines.append(
                "- No clear upward trend detected in the recent records.")

        analysis_lines.append("\n### 💡 Areas for Strategic Focus")
        if quiz_results_summary.strip():
            analysis_lines.append(
                "- Several incorrect quiz answers exist; focus on the types of questions shown in those examples.")
            analysis_lines.append(
                "- Use short targeted practice sessions on the weakest subtopics.")
        else:
            analysis_lines.append(
                "- No recent incorrect quiz data available to analyze. Consider taking a short diagnostic quiz.")

        analysis_lines.append("\n### 🚀 Recommended Next Steps")
        analysis_lines.append(
            "1. Schedule two 45-minute targeted practice sessions this week focusing on the top weak area.")
        analysis_lines.append(
            "2. Generate a focused Test Prep path for the weakest subsection.")
        analysis_lines.append(
            "3. Take one timed mini-quiz (10 questions) and review incorrect answers within 24 hours.")

        analysis_lines.append("\n### ✏️ Quick Micro-Quiz")
        analysis_lines.append(
            "Try a 10-question mixed quiz focusing on the weakest subsection; aim for 80%+ accuracy.")

        return "\n".join(analysis_lines)
    except Exception as e:
        print(f"Error in local tracker analysis: {e}")
        return "AI analysis is currently unavailable. Please try again later."


@app.route('/api/tracker-analysis')
@login_required
def tracker_analysis(user):
    analysis_text = _get_tracker_ai_analysis(user)
    return jsonify({"analysis": analysis_text})
# --- Standard Routes ---


def render_react(page, bootstrap=None, title=None, status=200):
    """Render the React application with server-verified bootstrap data."""
    data = dict(bootstrap or {})
    data['csrfToken'] = _csrf_token()
    g.csp_nonce = secrets.token_urlsafe(18)
    return render_template(
        "react_app.html",
        page=page,
        bootstrap=data,
        title=title or "Mentics",
        csp_nonce=g.csp_nonce,
    ), status


def _optional_number(value, minimum, maximum, label, *, integer=True):
    text = str(value or '').strip()
    if not text:
        return ''
    try:
        number = float(text)
    except (TypeError, ValueError) as error:
        raise ValueError(f'{label} must be a number.') from error
    if not minimum <= number <= maximum:
        raise ValueError(f'{label} must be between {minimum} and {maximum}.')
    return str(int(number)) if integer else str(round(number, 2))


@app.route("/privacy")
def privacy():
    return render_react("privacy", title="Privacy Policy | Mentics")


@app.route("/terms")
def terms():
    return render_react("terms", title="Terms of Service | Mentics")


@app.route("/")
def home():
    is_logged_in = "user" in session
    return render_react("landing", {"isLoggedIn": is_logged_in}, "Mentics | Stop Guessing. Start Achieving.")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()[:254]
        name = request.form.get("name", "").strip()[:100]
        raw_password = request.form.get("password", "")
        valid_email = re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email)
        if not valid_email or not name or not 8 <= len(raw_password) <= 128:
            return render_react("signup", {
                "error": "Enter your name, a valid email, and a password between 8 and 128 characters."
            }, "Create Account | Mentics", 400)
        if db.select_one("users", where={"email": email}):
            return render_react("signup", {"error": "Email already exists!"}, "Create Account | Mentics", 409)
        password = generate_password_hash(raw_password)
        try:
            user_id = db.insert("users", {
                "email": email, "password": password, "name": name,
                "stats": json.dumps({
                    "sat_ebrw": "", "sat_math": "", "act_math": "",
                    "act_reading": "", "act_science": "", "gpa": "", "milestones": 0
                })
            })

            db.insert("gamification_stats", {
                      "user_id": user_id, "points": 0, "current_streak": 0})

            session.clear()
            session["user"] = email
            session["user_id"] = user_id
            session.permanent = True
            return redirect(url_for("onboarding"))
        except Exception as e:
            print(f"Signup error: {e}")
            return render_react("signup", {"error": "Unable to create the account right now."}, "Create Account | Mentics", 500)
    return render_react("signup", title="Create Account | Mentics")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("dashboard"))
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user_record = db.select_one("users", where={"email": email})
        if len(password) <= 128 and user_record and check_password_hash(user_record['password'], password):
            session.clear()
            session["user"] = user_record['email']
            session["user_id"] = user_record['id']
            session.permanent = True
            return redirect(url_for("dashboard"))
        error = "Invalid credentials"
    return render_react("login", {"error": error}, "Sign In | Mentics")

# NEW: Google Login Route


@app.route('/google-login')
def google_login():
    redirect_uri = url_for('authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

# NEW: Google Authorize Route (Callback) - UPDATED


@app.route('/authorize')
def authorize():
    token = oauth.google.authorize_access_token()
    user_info = oauth.google.parse_id_token(token, nonce=session.get('nonce'))

    user_record = db.select_one("users", where={"email": user_info['email']})

    if user_record:
        authenticated_email = user_record['email']
        authenticated_id = user_record['id']
    else:

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
        db.insert("gamification_stats", {
                  "user_id": user_id, "points": 0, "current_streak": 0})

        authenticated_email = user_info['email']
        authenticated_id = user_id

    session.clear()
    session["user"] = authenticated_email
    session["user_id"] = authenticated_id
    session.permanent = True

    return redirect(url_for("onboarding"))


@app.route("/logout", methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route('/onboarding', methods=['GET', 'POST'])
@login_required
def onboarding(user):
    if user.data['onboarding_completed']:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        goal = request.form.get('goal')
        learning_style = request.form.get('learning_style')
        if goal not in {'test_prep', 'college_planning'} or learning_style not in {
            'visual', 'auditory', 'reading_writing', 'kinesthetic'
        }:
            return render_react("onboarding", {
                "error": "Choose a primary goal and learning style to continue.",
                "name": user.get_name(),
            }, "Welcome | Mentics", 400)
        onboarding_data = {
            'goal': goal,
            'learning_style': learning_style,
            'anxieties': request.form.get('anxieties', '').strip()[:1000]
        }
        db.update('users', {
            'onboarding_data': json.dumps(onboarding_data),
            'onboarding_completed': True
        }, {'id': user.data['id']})
        return redirect(url_for('dashboard'))

    return render_react("onboarding", {"name": user.get_name()}, "Welcome | Mentics")


@app.route('/set-timezone', methods=['POST'])
def set_timezone():
    data = request.get_json(silent=True) or {}
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

    user_tz_str = session.get('timezone', 'UTC')
    try:
        user_tz = ZoneInfo(user_tz_str)
    except ZoneInfoNotFoundError:
        user_tz = ZoneInfo("UTC")

    today = datetime.now(user_tz).date()
    seven_days_ago = today - timedelta(days=6)

    activity_counts = {}
    labels = []
    for i in range(7):
        current_date = seven_days_ago + timedelta(days=i)
        labels.append(current_date.strftime('%a'))
        activity_counts[current_date] = 0

    recent_logs = db.execute(
        "SELECT created_at FROM activity_log WHERE user_id = ? AND date(created_at) >= ?",
        (user_id, seven_days_ago.strftime('%Y-%m-%d'))
    )

    if recent_logs:
        for log in recent_logs:
            utc_dt = _parse_db_datetime(log['created_at']).astimezone(ZoneInfo("UTC"))

            user_local_date = utc_dt.astimezone(user_tz).date()

            if user_local_date in activity_counts:
                activity_counts[user_local_date] += 1

    activity_data = {
        "labels": labels,
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
            try:
                user_tz_str = session.get('timezone', 'UTC')
                user_today = datetime.now(ZoneInfo(user_tz_str)).date()
            except ZoneInfoNotFoundError:
                user_today = date.today()
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

    return render_react("dashboard", {
        "name": name,
        "testPrepCompleted": test_prep_completed_current,
        "collegePlanningCompleted": college_planning_completed_current,
        "gpa": stats.get("gpa") or "—",
        "satTotal": sat_total or "—",
        "actAverage": act_average or "—",
        "recentActivities": recent_activities,
        "activityData": activity_data,
        "testDateInfo": test_date_info,
        "earnedAchievements": earned_achievements,
        "gameStats": game_stats,
    }, "Dashboard | Mentics")


@app.route("/api/get-suggestion")
@login_required
def get_suggestion(user):
    """A new route to fetch the AI suggestion asynchronously."""
    today = datetime.now(ZoneInfo("UTC")).date().isoformat()
    cached = session.get("daily_ai_suggestion")
    if isinstance(cached, dict) and cached.get("date") == today:
        return jsonify({"suggestion": cached.get("value", "")})
    suggestion = _get_proactive_ai_suggestions(user)
    session["daily_ai_suggestion"] = {"date": today, "value": suggestion[:500]}
    return jsonify({"suggestion": suggestion})


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account(user):
    if request.method == 'POST':
        form_type = request.form.get('form_type')

        def account_error(message, status=400):
            user.load_user()
            return render_react("account", {
                "name": user.data.get("name", ""),
                "email": user.data.get("email", ""),
                "error": message,
            }, "Account | Mentics", status)

        if form_type == 'name':
            new_name = request.form.get('name', '').strip()[:100]
            if not new_name:
                return account_error("Name cannot be empty.")
            db.update('users', {'name': new_name}, {'id': user.data['id']})

        elif form_type == 'email':
            new_email = request.form.get('email', '').strip().lower()[:254]
            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", new_email):
                return account_error("Enter a valid email address.")
            existing_user = db.select('users', where={'email': new_email})
            if not existing_user or existing_user[0]['id'] == user.data['id']:
                db.update('users', {'email': new_email},
                          {'id': user.data['id']})
                session['user'] = new_email
            else:
                return account_error("That email address is already in use.", 409)

        elif form_type == 'password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')

            if not check_password_hash(user.data['password'], current_password):
                return account_error("Your current password is incorrect.")
            if not 8 <= len(new_password) <= 128:
                return account_error("New password must be between 8 and 128 characters.")
            if new_password != confirm_password:
                return account_error("New passwords do not match.")
            hashed_password = generate_password_hash(new_password)
            db.update('users', {'password': hashed_password}, {
                      'id': user.data['id']})
        else:
            return account_error("Unknown account update.")

        return redirect(url_for('account', updated='1'))

    user.load_user()
    return render_react("account", {
        "name": user.data.get("name", ""),
        "email": user.data.get("email", ""),
        "updated": request.args.get("updated") == "1",
    }, "Account | Mentics")


@app.route("/dashboard/test-path-builder", methods=["GET", "POST"])
@login_required
def test_path_builder(user):
    stats = user.get_stats()

    current_test_path_info = stats.get("test_path", {})

    if request.method == "POST":
        try:
            test_focus = request.form.get("test_focus", "")
            if test_focus not in {'sat', 'act', 'both'}:
                raise ValueError("Choose SAT, ACT, or both.")
            test_date = request.form.get("test_date", "").strip()
            if test_date:
                date.fromisoformat(test_date)
            weaknesses = request.form.get("weaknesses", "").strip()[:2000]
            if not weaknesses:
                raise ValueError("Tell Mentics where you need the most help.")
            test_path = {
                "test_focus": test_focus,
                "desired_sat": _optional_number(request.form.get("desired_sat"), 400, 1600, "Desired SAT"),
                "desired_act": _optional_number(request.form.get("desired_act"), 1, 36, "Desired ACT"),
                "current_sat_ebrw": _optional_number(request.form.get("current_sat_ebrw"), 200, 800, "Current SAT reading and writing"),
                "current_sat_math": _optional_number(request.form.get("current_sat_math"), 200, 800, "Current SAT math"),
                "current_act_composite": _optional_number(request.form.get("current_act_composite"), 1, 36, "Current ACT composite"),
                "current_act_math": _optional_number(request.form.get("current_act_math"), 1, 36, "Current ACT math"),
                "current_act_reading": _optional_number(request.form.get("current_act_reading"), 1, 36, "Current ACT reading"),
                "current_act_science": _optional_number(request.form.get("current_act_science"), 1, 36, "Current ACT science"),
                "strengths": request.form.get("strengths", "").strip()[:2000],
                "weaknesses": weaknesses,
                "test_date": test_date,
                "hours_per_week": _optional_number(request.form.get("hours_per_week"), 1, 40, "Hours per week"),
            }
        except ValueError as error:
            return render_react("test-builder", {
                "name": user.get_name(), "error": str(error), **request.form.to_dict()
            }, "Build Test Path | Mentics", 400)
        stats["test_path"] = test_path
        user.set_stats(stats)
        _generate_and_save_new_test_path(

            user.data['id'], test_path)
        return redirect(url_for("test_path_view"))

    return render_react("test-builder", {
        "name": user.get_name(),
        **current_test_path_info,
    }, "Build Test Path | Mentics")


@app.route("/dashboard/test-path-view")
@login_required
def test_path_view(user):
    return render_react("path", {
        "category": "Test Prep",
        "name": user.get_name(),
    }, "Test Path | Mentics")


@app.route("/dashboard/college-path-builder", methods=["GET", "POST"])
@login_required
def college_path_builder(user):
    stats = user.get_stats()
    if request.method == "POST":
        grade = request.form.get('current_grade', '')
        planning_stage = request.form.get('planning_stage', '')
        if grade not in {'9', '10', '11', '12'} or planning_stage not in {'exploring', 'researching', 'applying'}:
            return render_react("college-builder", {
                "name": user.get_name(), "error": "Choose a valid grade and planning stage.",
                "grade": grade, "planning_stage": planning_stage,
                "majors": request.form.get('interested_majors', '').strip()[:2000],
                "target_colleges": request.form.get('target_colleges', '').strip()[:2000],
            }, "Build College Path | Mentics", 400)
        college_context = {
            'grade': grade,
            'planning_stage': planning_stage,
            'majors': request.form.get('interested_majors', '').strip()[:2000],
            'target_colleges': request.form.get('target_colleges', '').strip()[:2000]
        }
        stats['college_path'] = college_context
        user.set_stats(stats)
        _generate_and_save_new_college_path(user.data['id'], college_context)
        return redirect(url_for('college_path_view'))
    return render_react("college-builder", {
        "name": user.get_name(),
        **stats.get('college_path', {}),
    }, "Build College Path | Mentics")


@app.route('/dashboard/college-path-view')
@login_required
def college_path_view(user):
    return render_react("path", {
        "category": "College Planning",
        "name": user.get_name(),
    }, "College Path | Mentics")

# --- Stats & Tracker Routes ---


@app.route("/dashboard/stats", methods=["GET"])
@login_required
def stats(user):
    stats = user.get_stats()
    user_id = user.data['id']
    all_tasks = db.select("paths", where={"user_id": user_id})

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

    act_average = None
    if act_scores:
        act_average = round(sum(act_scores) / len(act_scores))

    total_test_prep_completed = sum(
        1 for t in all_tasks if t['is_completed'] and t['category'] == 'Test Prep')
    total_college_planning_completed = sum(
        1 for t in all_tasks if t['is_completed'] and t['category'] == 'College Planning')

    return render_react("stats", {
        "name": user.get_name(),
        "gpa": stats.get("gpa", ""),
        "satEbrw": sat_ebrw,
        "satMath": sat_math,
        "satTotal": sat_total,
        "actMath": stats.get("act_math", ""),
        "actReading": stats.get("act_reading", ""),
        "actScience": stats.get("act_science", ""),
        "actAverage": act_average,
        "totalTestPrepCompleted": total_test_prep_completed,
        "totalCollegePlanningCompleted": total_college_planning_completed,
    }, "Progress | Mentics")


@app.route("/dashboard/stats/edit", methods=["GET", "POST"])
@login_required
def edit_stats(user):
    stats = user.get_stats()
    if request.method == "POST":
        try:
            updated_stats = {
                "gpa": _optional_number(request.form.get("gpa"), 0, 5, "GPA", integer=False),
                "sat_ebrw": _optional_number(request.form.get("sat_ebrw"), 200, 800, "SAT reading and writing"),
                "sat_math": _optional_number(request.form.get("sat_math"), 200, 800, "SAT math"),
                "act_math": _optional_number(request.form.get("act_math"), 1, 36, "ACT math"),
                "act_reading": _optional_number(request.form.get("act_reading"), 1, 36, "ACT reading"),
                "act_science": _optional_number(request.form.get("act_science"), 1, 36, "ACT science"),
            }
        except ValueError as error:
            return render_react("edit-stats", {
                "name": user.get_name(), "error": str(error),
                "satEbrw": request.form.get("sat_ebrw", ""),
                "satMath": request.form.get("sat_math", ""),
                "actMath": request.form.get("act_math", ""),
                "actReading": request.form.get("act_reading", ""),
                "actScience": request.form.get("act_science", ""),
                "gpa": request.form.get("gpa", ""),
            }, "Update Progress | Mentics", 400)

        for key, value in updated_stats.items():

            if stats.get(key) != value and value:
                stats[key] = value
                log_activity(user.data['id'], 'stat_updated', {
                             'stat_name': key.upper(), 'stat_value': value})

        user.set_stats(stats)
        return redirect(url_for("stats"))

    return render_react("edit-stats", {
        "name": user.get_name(),
        "satEbrw": stats.get("sat_ebrw", ""),
        "satMath": stats.get("sat_math", ""),
        "actMath": stats.get("act_math", ""),
        "actReading": stats.get("act_reading", ""),
        "actScience": stats.get("act_science", ""),
        "gpa": stats.get("gpa", ""),
    }, "Update Progress | Mentics")


# --- API ROUTES ---

@app.route('/api/submit_quiz_results', methods=['POST'])
@login_required
def submit_quiz_results(user):
    data = request.get_json(silent=True) or {}
    try:
        return jsonify(_score_assessment_results(user.data['id'], data.get('results'), 'quiz'))
    except ValueError as error:
        return jsonify({"success": False, "error": str(error)}), 400


@app.route('/api/test-path-status')
@login_required
def test_path_status(user):
    user_id = user.data['id']

    query = "SELECT 1 FROM paths WHERE user_id=? AND is_active=True AND category='Test Prep' LIMIT 1"

    result = db.execute_for_one(query, (user_id,))
    return jsonify({"has_path": bool(result)})


@app.route('/api/college-path-status')
@login_required
def college_path_status(user):
    user_id = user.data['id']

    query = "SELECT 1 FROM paths WHERE user_id=? AND is_active=True AND category='College Planning' LIMIT 1"

    result = db.execute_for_one(query, (user_id,))
    return jsonify({"has_path": bool(result)})


@app.route("/api/tasks", methods=['GET', 'POST'])
@login_required
def api_tasks(user):
    user_id = user.data['id']
    stats = user.get_stats()
    category = request.args.get('category', 'Test Prep')
    try:
        if category not in {'Test Prep', 'College Planning'}:
            return jsonify({"error": "Invalid category"}), 400

        active_path = db.select(
            "paths",
            where={
                "user_id": user_id,
                "is_active": True,
                "category": category,
            },
            order_by="task_order ASC"
        )

        if request.method == "POST" or not active_path:
            chat_record_list = db.select("chat_conversations", where={
                "user_id": user_id, "category": category})
            chat_history = json.loads(
                chat_record_list[0]['history']) if chat_record_list else []
            try:
                if category == 'College Planning':
                    college_context = stats.get("college_path", {})
                    tasks = _generate_and_save_new_college_path(
                        user_id, college_context, chat_history)
                else:
                    test_path_info = stats.get("test_path", {})
                    tasks = _generate_and_save_new_test_path(
                        user_id, test_path_info, chat_history)
            except Exception:
                app.logger.exception("Path generation failed for user %s", user_id)
                return jsonify({
                    "error": "I couldn't generate a complete five-step path. Your current path is unchanged; please try again."
                }), 502
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
                    "is_skipped": bool(r.get('is_skipped', False)),
                    "type": r['type'],
                    "stat_to_update": r['stat_to_update'],
                    "due_date": r['due_date'],
                    "is_user_added": bool(r['is_user_added']),
                    "subtasks": subtasks,
                    "task_format": r.get('task_format', 'link'),
                    "task_content_id": r.get('task_content_id')
                })
            return jsonify(tasks_with_subtasks)

        return jsonify([])
    except Exception as e:
        print(f"API tasks error for category {category}: {e}")
        return jsonify({"error": "An error occurred"}), 500


@app.route('/api/quiz/<int:task_id>')
@login_required
def get_quiz(user, task_id):

    task_info = db.select(
        "paths", where={"id": task_id, "user_id": user.data['id'], "is_active": True})
    if not task_info or task_info[0]['task_format'] != 'quiz':
        return jsonify({"error": "Quiz not found or task is not a quiz"}), 404
    if _has_incomplete_earlier_task(user.data['id'], task_info[0]):
        return jsonify({"error": "Complete the earlier path step first."}), 409

    quiz_id = task_info[0]['task_content_id']
    quiz_details = db.select("quizzes", where={"id": quiz_id})
    if not quiz_details:
        return jsonify({"error": "Quiz details not found"}), 404

    questions_raw = db.select("quiz_questions", where={"quiz_id": quiz_id})
    questions = []
    for q in questions_raw:
        questions.append({
            "id": q['id'],
            "source_or_prompt": q.get('source_or_prompt'),
            "question_text": q['question_text'],
            "options": json.loads(q['options'])
        })

    return jsonify({
        "title": quiz_details[0]['title'],
        "questions": questions
    })


@app.route('/api/skip_task', methods=['POST'])
@login_required
def api_skip_task(user):
    user_id = user.data['id']
    data = request.get_json(silent=True) or {}
    task_id = data.get("taskId")

    if not task_id:
        return jsonify({"success": False, "error": "A task ID is required."}), 400

    task_info = db.select_one("paths", where={
        "id": task_id, "user_id": user_id, "is_active": True
    })
    if not task_info:
        return jsonify({"success": False, "error": "Task not found."}), 404
    if task_info['is_completed']:
        return jsonify({"success": True, "already_completed": True})

    blocked = db.execute_for_one(
        """SELECT id FROM paths
           WHERE user_id=? AND category=? AND is_active=True
             AND task_order<? AND is_completed=False LIMIT 1""",
        (user_id, task_info['category'], task_info['task_order'])
    )
    if blocked:
        return jsonify({"success": False, "error": "Complete the earlier path step first."}), 409

    claimed = db.execute_write(
        "UPDATE paths SET is_completed=?, is_skipped=? WHERE id=? AND user_id=? AND is_completed=?",
        (True, True, task_id, user_id, False)
    )
    if not claimed:
        return jsonify({"success": True, "already_completed": True})

    description = task_info['description']
    category = task_info['category']
    log_activity(user_id, 'task_skipped', {
        'description': description,
        'category': category,
        'task_format': task_info.get('task_format')
    })
    return jsonify({"success": True, "skipped": True})


@app.route("/api/update_task_status", methods=['POST'])
@login_required
def api_update_task_status(user):
    user_id = user.data['id']
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    task_id = data.get("taskId")

    if status not in {'complete', 'skip'} or not task_id:
        return jsonify({"success": False, "error": "A valid task and status are required."}), 400
    task_info = db.select_one("paths", where={
        "id": task_id, "user_id": user_id, "is_active": True
    })
    if not task_info:
        return jsonify({"success": False, "error": "Task not found."}), 404
    if task_info['is_completed']:
        return jsonify({"success": True, "already_completed": True})
    blocked = db.execute_for_one(
        """SELECT id FROM paths
           WHERE user_id=? AND category=? AND is_active=True
             AND task_order<? AND is_completed=False LIMIT 1""",
        (user_id, task_info['category'], task_info['task_order'])
    )
    if blocked:
        return jsonify({"success": False, "error": "Complete the earlier path step first."}), 409
    if status == 'skip':
        claimed = db.execute_write(
            "UPDATE paths SET is_completed=?, is_skipped=? WHERE id=? AND user_id=? AND is_completed=?",
            (True, True, task_id, user_id, False)
        )
        if claimed:
            description = task_info['description']
            category = task_info['category']
            log_activity(user_id, 'task_skipped', {
                         'description': description, 'category': category, 'task_format': task_info.get('task_format')})
            return jsonify({"success": True, "skipped": True})
        return jsonify({"success": True, "already_completed": True})

    claimed = db.execute_write(
        "UPDATE paths SET is_completed=?, is_skipped=? WHERE id=? AND user_id=? AND is_completed=?",
        (True, False, task_id, user_id, False)
    )
    if claimed:
        description = task_info['description']
        category = task_info['category']
        task_type = task_info['type']
        log_activity(user_id, 'task_completed', {
                     'description': description, 'category': category})

        # --- GAMIFICATION LOGIC ---
        points_to_add = 25 if task_type == 'milestone' else 10
        if "boss battle" in description.lower():
            points_to_add = 100

        game_stats_rows = db.select(
            "gamification_stats", where={"user_id": user_id})
        if not game_stats_rows:
            db.insert("gamification_stats", {
                "user_id": user_id, "points": 0, "current_streak": 0
            })
            game_stats_rows = db.select(
                "gamification_stats", where={"user_id": user_id})
        game_stats_row = game_stats_rows[0]
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
            new_streak = game_stats['streak']
        elif last_completed_date == yesterday:
            new_streak += 1
        else:
            new_streak = 1

        db.update("gamification_stats", {
            "points": game_stats['points'] + points_to_add,
            "current_streak": new_streak,
            "last_completed_date": today.isoformat()
        }, where={"user_id": user_id})
    else:
        return jsonify({"success": True, "already_completed": True})

    return jsonify({"success": True})


def _regenerate_path_from_chat(user_id, stats, category, history):
    """Generate, persist, and return a path without leaking control messages."""
    try:
        if category == 'College Planning':
            college_context = stats.get("college_path", {})
            new_tasks = _generate_and_save_new_college_path(
                user_id, college_context, chat_history=history)
        else:
            test_path_info = stats.get("test_path", {})
            new_tasks = _generate_and_save_new_test_path(
                user_id, test_path_info, chat_history=history)
        if len(new_tasks) != 5:
            raise ValueError("Regeneration did not save exactly five tasks.")
    except Exception:
        app.logger.exception(
            "Chat path regeneration failed for user %s (%s)", user_id, category
        )
        return jsonify({
            "error": "I couldn't generate a complete five-step path. Your current path is unchanged; please try again."
        }), 502

    reply = "Your new five-step path is ready. I shaped it around your latest request and our conversation."
    history.append({"role": "assistant", "content": reply})
    try:
        db.upsert("chat_conversations", {
            "user_id": user_id,
            "category": category,
            "history": json.dumps(history)
        }, conflict_target=["user_id", "category"])
    except Exception:
        # The path is already committed. A history-write failure should not
        # turn a successful regeneration into a misleading client error.
        app.logger.exception(
            "Path regenerated but chat history could not be saved for user %s",
            user_id,
        )
    return jsonify({"new_path": new_tasks, "reply": reply})


def _is_path_regeneration_control(reply):
    cleaned = (reply or "").strip().strip('`').strip()
    return cleaned == PATH_REGENERATION_CONTROL


@app.route("/api/chat", methods=['POST'])
@login_required
def api_chat(user):
    user_id = user.data['id']
    stats = user.get_stats()
    data = request.get_json(silent=True) or {}
    history = data.get("history", [])
    category = request.args.get('category', 'Test Prep')

    if category not in {'Test Prep', 'College Planning'} or not isinstance(history, list):
        return jsonify({"error": "Invalid chat request"}), 400
    if len(history) > 50:
        history = history[-50:]
    if any(
        not isinstance(message, dict)
        or message.get('role') not in {'user', 'assistant'}
        or not isinstance(message.get('content'), str)
        or len(message['content']) > 4000
        for message in history
    ):
        return jsonify({"error": "Invalid chat history"}), 400

    if not history or (len(history) == 1 and history[0]['role'] == 'user' and history[0]['content'] == 'INITIAL_MESSAGE'):
        history = []
    elif history[-1]['role'] != 'user':
        return jsonify({"error": "The latest chat message must be from the user."}), 400

    user_message = next((
        message['content'] for message in reversed(history)
        if message['role'] == 'user'
    ), "")
    if _is_path_regeneration_request(user_message):
        return _regenerate_path_from_chat(user_id, stats, category, history)

    # Fetch tracker data only for regular coaching replies. Regeneration already
    # gathers the richer task, assessment, and tracker context it needs.
    stat_history = _get_stat_history_for_prompt(user_id)

    if category == 'College Planning':
        reply = _get_college_planning_ai_chat_response(
            history, stats, stat_history, user_id)
    else:
        reply = _get_test_prep_ai_chat_response(
            history, stats, stat_history, user_id)

    if _is_path_regeneration_control(reply):
        return _regenerate_path_from_chat(user_id, stats, category, history)

    history.append({"role": "assistant", "content": reply})

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
    if category not in {'Test Prep', 'College Planning'}:
        return jsonify({"error": "Invalid category"}), 400
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
    data = request.get_json(silent=True) or {}
    category = data.get('category')
    if category not in {'Test Prep', 'College Planning'}:
        return jsonify({"success": False, "error": "Invalid category"}), 400
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
    data = request.get_json(silent=True) or {}
    stat_name = data.get("stat_name")
    stat_value = data.get("stat_value")

    stat_ranges = {
        'gpa': (0, 5),
        'sat_ebrw': (200, 800),
        'sat_math': (200, 800),
        'sat_total': (400, 1600),
        'act_math': (1, 36),
        'act_reading': (1, 36),
        'act_science': (1, 36),
        'act_composite': (1, 36),
        'colleges_researched': (0, 1000),
        'applications_submitted': (0, 1000),
        'essay_progress': (1, 2),
    }

    if stat_name not in stat_ranges or stat_value is None:
        return jsonify({"success": False, "error": "Missing stat name or value"}), 400

    try:
        numeric_value = float(stat_value)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Stat value must be a number"}), 400
    minimum, maximum = stat_ranges[stat_name]
    if not minimum <= numeric_value <= maximum:
        return jsonify({
            "success": False,
            "error": f"{stat_name.replace('_', ' ').title()} must be between {minimum} and {maximum}"
        }), 400
    stat_value = round(numeric_value, 2) if stat_name == 'gpa' else int(numeric_value)

    try:

        db.insert("stat_history", {
            "user_id": user.data['id'], "stat_name": stat_name, "stat_value": stat_value
        })

        if stat_name not in ["sat_total", "act_composite"]:
            stats = user.get_stats()
            stats[stat_name] = stat_value
            user.set_stats(stats)

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
    data = request.get_json(silent=True) or {}
    description = data.get('description')
    category = data.get('category')
    due_date = data.get('due_date')

    if not description or category not in {'Test Prep', 'College Planning'}:
        return jsonify({"success": False, "error": "Description and category are required"}), 400
    description = str(description).strip()[:500]
    if not description:
        return jsonify({"success": False, "error": "Description is required"}), 400
    if due_date:
        try:
            date.fromisoformat(str(due_date))
        except ValueError:
            return jsonify({"success": False, "error": "Due date must be a valid date"}), 400

    personal_task_count = db.execute_for_one(
        """SELECT COUNT(*) AS task_count FROM paths
           WHERE user_id=? AND category=? AND is_active=True AND is_user_added=True""",
        (user_id, category)
    )
    if personal_task_count and personal_task_count['task_count'] >= 20:
        return jsonify({
            "success": False,
            "error": "This path already has 20 personal steps. Complete or regenerate it before adding more."
        }), 429

    latest_task_query = "SELECT MAX(task_order) as max_order FROM paths WHERE user_id=? AND category=? AND is_active=True"
    max_order_result = db.execute(latest_task_query, (user_id, category))
    new_order = (max_order_result[0]['max_order'] or 0) + 1

    task_id = db.insert("paths", {
        "user_id": user_id,
        "task_order": new_order,
        "description": description,
        "is_completed": False,
        "is_active": True,
        "type": "standard",
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
    data = request.get_json(silent=True) or {}
    parent_task_id = data.get('parent_task_id')
    description = data.get('description')

    if not parent_task_id or not description:
        return jsonify({"success": False, "error": "Parent task ID and description are required"}), 400

    parent_task = db.select_one('paths', where={
        'id': parent_task_id, 'user_id': user.data['id']
    })
    if not parent_task:
        return jsonify({"success": False, "error": "Task not found"}), 404
    description = str(description).strip()[:500]
    if not description:
        return jsonify({"success": False, "error": "Description is required"}), 400
    subtask_count = db.execute_for_one(
        "SELECT COUNT(*) AS subtask_count FROM subtasks WHERE parent_task_id=?",
        (parent_task_id,)
    )
    if subtask_count and subtask_count['subtask_count'] >= 30:
        return jsonify({"success": False, "error": "A task can have up to 30 notes and sub-steps."}), 429

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
    data = request.get_json(silent=True) or {}
    task_id = data.get('taskId')
    due_date = data.get('dueDate')

    if not task_id or not db.select_one('paths', where={
            'id': task_id, 'user_id': user.data['id']}):
        return jsonify({"success": False, "error": "Task not found"}), 404
    if due_date:
        try:
            date.fromisoformat(str(due_date))
        except ValueError:
            return jsonify({"success": False, "error": "Due date must be a valid date"}), 400
    db.update("paths", {"due_date": due_date}, where={
              "id": task_id, "user_id": user.data['id']})
    return jsonify({"success": True})


@app.route('/api/update_subtask', methods=['POST'])
@login_required
def update_subtask(user):
    data = request.get_json(silent=True) or {}
    subtask_id = data.get('subtaskId')
    is_completed = data.get('is_completed')

    if not isinstance(is_completed, bool):
        return jsonify({"success": False, "error": "Completion state must be true or false"}), 400

    owned_subtask = db.execute_for_one(
        """SELECT subtasks.id FROM subtasks
           JOIN paths ON paths.id = subtasks.parent_task_id
           WHERE subtasks.id=? AND paths.user_id=?""",
        (subtask_id, user.data['id'])
    )
    if not owned_subtask:
        return jsonify({"success": False, "error": "Subtask not found"}), 404
    db.update("subtasks", {"is_completed": is_completed},
              where={"id": subtask_id})
    return jsonify({"success": True})

# --- NEW ESSAY ANALYSIS ROUTE (with more granular feedback) ---


@app.route('/api/analyze_essay', methods=['POST'])
@login_required
def analyze_essay(user):
    data = request.get_json(silent=True) or {}
    essay_text = data.get('essay_text')
    essay_prompt = data.get(
        'essay_prompt', 'a general college application essay')

    if not essay_text:
        return jsonify({"error": "Essay text is required."}), 400
    if len(essay_text) > 20000:
        return jsonify({"error": "Essay text must be 20,000 characters or fewer."}), 400
    essay_prompt = str(essay_prompt).strip()[:500]
    if gemini_client is None:
        return jsonify({"error": "AI essay feedback is not configured."}), 503

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
        feedback = _generate_text(
            prompt,
            max_output_tokens=1800,
            thinking_level="low",
        )
        return jsonify({"feedback": feedback})
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
        return _generate_text(prompt, max_output_tokens=120)
    except Exception as e:
        print(f"Error in proactive suggestion generation: {e}")
        return "Welcome to Mentics! Let's get started on your path to success."


# --- NEW SOCIAL ROUTES ---
@app.route('/leaderboard')
@login_required
def leaderboard(user):

    leaderboard_data = db.execute(
        """
        SELECT u.name, g.points
        FROM gamification_stats g
        JOIN users u ON g.user_id = u.id
        ORDER BY g.points DESC
        LIMIT 10
        """
    )
    return render_react("leaderboard", {
        "name": user.get_name(),
        "leaderboard": [dict(row) for row in leaderboard_data],
    }, "Leaderboard | Mentics")


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

    return render_react("forum", {
        "name": user.get_name(),
        "posts": posts_with_replies,
        "todaysThreads": todays_threads,
        "searchQuery": search_query,
    }, "Community | Mentics")


@app.route('/api/posts', methods=['POST'])
@login_required
def create_post(user):
    data = request.get_json(silent=True) or {}
    title = data.get('title')
    content = data.get('content')
    if title and content:
        title = str(title).strip()[:200]
        content = str(content).strip()[:5000]
        if not title or not content:
            return jsonify({'success': False, 'error': 'Title and content are required'}), 400
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
    data = request.get_json(silent=True) or {}
    post_id = data.get('post_id')
    content = data.get('content')
    if post_id and content:
        if not db.select_one('forum_posts', where={'id': post_id}):
            return jsonify({'success': False, 'error': 'Post not found'}), 404
        content = str(content).strip()[:5000]
        if not content:
            return jsonify({'success': False, 'error': 'Reply content is required'}), 400
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


# Use hosted Postgres in production and zero-config SQLite for development.
DATABASE = os.getenv('DATABASE_URL')
if is_production and not DATABASE:
    raise RuntimeError("DATABASE_URL must be configured in production; local SQLite is not persistent.")
if not DATABASE:
    os.makedirs(app.instance_path, exist_ok=True)
    DATABASE = os.path.join(app.instance_path, 'users.db')

db = DatabaseHandler(DATABASE)

with app.app_context():
    print(f"Connecting to {'PostgreSQL' if db.is_postgres else DATABASE}...")
    try:
        init_db()
        print("Database schema check complete. All tables and columns are present.")
    except Exception as e:
        print(f"!!! CRITICAL: FAILED TO INITIALIZE OR MIGRATE DATABASE: {e}")
        if is_production:
            raise
if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
