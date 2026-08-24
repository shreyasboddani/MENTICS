# Copyright © 2026 Mentics
# All Rights Reserved.
from flask import Flask, Response, render_template, request, redirect, url_for, session, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from dbhelper import DatabaseHandler
from userhelper import User
import learning
import ratelimit
import seo
from ratelimit import rate_limit
from functools import wraps
import json
import hmac
import mimetypes
import os
import secrets
from dotenv import load_dotenv
import re
from pathlib import Path
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
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
gemini_client = None
gemini_types = None
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
    if is_production and request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        response.headers['Vercel-CDN-Cache-Control'] = 'public, max-age=31536000'
        response.headers.pop('Vary', None)
    elif session.get('user'):
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


# Ceiling on write traffic from any single caller. Individual endpoints below
# set tighter, purpose-specific limits; this only stops broad hammering.
GLOBAL_WRITE_LIMIT = os.getenv('RATE_LIMIT_WRITES', '120/minute')
CSRF_EXEMPT_PATHS = {'/api/import_official_questions'}


@app.before_request
def protect_state_changing_requests():
    if request.method not in {'POST', 'PUT', 'PATCH', 'DELETE'}:
        return None
    allowed, retry_after = ratelimit.check(GLOBAL_WRITE_LIMIT, name='global_write')
    if not allowed:
        return ratelimit.too_many(retry_after)
    # CSRF defends against a browser attaching the session cookie to a forged
    # request. Endpoints that authenticate with an explicit header instead of a
    # cookie carry no such ambient authority, so the token check does not apply.
    if request.path in CSRF_EXEMPT_PATHS:
        return None
    expected = session.get('_csrf_token')
    supplied = request.headers.get('X-CSRF-Token') or request.form.get('_csrf_token')
    if expected and supplied and hmac.compare_digest(expected, supplied):
        return None
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Your session expired. Refresh the page and try again.'}), 400
    return 'Invalid or expired request. Refresh the page and try again.', 400


oauth = None


def _get_oauth():
    """Load the optional OAuth stack only when Google sign-in is used."""
    global oauth
    if oauth is None:
        from authlib.integrations.flask_client import OAuth
        oauth = OAuth(app)
        oauth.register(
            name='google',
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            client_kwargs={'scope': 'openid email profile'}
        )
    return oauth


def init_db():
    ratelimit.ensure_table(db)
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
    db.create_table("sat_battles", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "status": "TEXT NOT NULL DEFAULT 'waiting'",
        "challenger_id": "INTEGER NOT NULL",
        "challenger_name": "TEXT NOT NULL",
        "opponent_id": "INTEGER",
        "opponent_name": "TEXT",
        "questions": "TEXT NOT NULL",
        "challenger_answers": "TEXT",
        "opponent_answers": "TEXT",
        "started_at": "TIMESTAMP",
        "challenger_finished_at": "TIMESTAMP",
        "opponent_finished_at": "TIMESTAMP",
        "completed_at": "TIMESTAMP",
        "winner_id": "INTEGER",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "FOREIGN KEY(challenger_id)": "REFERENCES users(id) ON DELETE CASCADE",
        "FOREIGN KEY(opponent_id)": "REFERENCES users(id) ON DELETE CASCADE"
    })
    db.create_table("sat_battle_stats", {
        "user_id": "INTEGER PRIMARY KEY",
        "user_name": "TEXT NOT NULL",
        "rating": "INTEGER NOT NULL DEFAULT 1000",
        "wins": "INTEGER NOT NULL DEFAULT 0",
        "losses": "INTEGER NOT NULL DEFAULT 0",
        "draws": "INTEGER NOT NULL DEFAULT 0",
        "battles_played": "INTEGER NOT NULL DEFAULT 0",
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

    db.add_column("sprint_questions", "source_or_prompt", "TEXT")

    db.create_table("official_questions", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "test_type": "TEXT NOT NULL",
        "subject": "TEXT NOT NULL",
        "topic": "TEXT NOT NULL",
        "difficulty": "TEXT",
        "question_text": "TEXT NOT NULL",
        "options": "TEXT NOT NULL",
        "correct_option": "INTEGER NOT NULL",
        "explanation": "TEXT",
        "source_url": "TEXT",
        "source_or_prompt": "TEXT",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    })
    db.execute("CREATE INDEX IF NOT EXISTS idx_official_questions_subject_topic ON official_questions (test_type, subject, topic)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_official_questions_difficulty ON official_questions (difficulty)")

    db.create_table("strategy_articles", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "task_id": "INTEGER NOT NULL UNIQUE",
        "title": "TEXT NOT NULL",
        "content": "TEXT NOT NULL",
        "FOREIGN KEY(task_id)": "REFERENCES paths(id) ON DELETE CASCADE"
    })

    db.add_column("paths", "secondary_content_id", "INTEGER")

    # --- Adaptive lesson engine ---
    # A path step now carries the skill it targets so mastery survives across
    # regenerated paths, and node_type distinguishes teaching from drilling.
    for column, column_type in {
        "skill_key": "TEXT",
        "skill_label": "TEXT",
        "subject": "TEXT",
        "node_type": "TEXT",
        "objective": "TEXT",
        "xp_reward": "INTEGER DEFAULT 10",
        "unit_title": "TEXT",
        # High-water mark of XP already granted for this step, so replaying a
        # drill cannot mint points over and over.
        "xp_awarded": "INTEGER DEFAULT 0",
    }.items():
        db.add_column("paths", column, column_type)

    db.create_table("lessons", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "task_id": "INTEGER NOT NULL UNIQUE",
        "title": "TEXT NOT NULL",
        "skill_key": "TEXT",
        "skill_label": "TEXT",
        "subject": "TEXT",
        "objective": "TEXT",
        "intro": "TEXT",
        "recap": "TEXT",
        "xp_reward": "INTEGER DEFAULT 30",
        "FOREIGN KEY(task_id)": "REFERENCES paths(id) ON DELETE CASCADE"
    })

    db.create_table("lesson_steps", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "lesson_id": "INTEGER NOT NULL",
        "step_order": "INTEGER NOT NULL",
        "step_type": "TEXT NOT NULL",
        "title": "TEXT",
        "body": "TEXT",
        "worked_example": "TEXT",
        "takeaway": "TEXT",
        "trap": "TEXT",
        "source_or_prompt": "TEXT",
        "question_text": "TEXT",
        "options": "TEXT",
        "correct_option": "INTEGER",
        "explanation": "TEXT",
        "FOREIGN KEY(lesson_id)": "REFERENCES lessons(id) ON DELETE CASCADE"
    })

    db.create_table("lesson_progress", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id": "INTEGER NOT NULL",
        "lesson_id": "INTEGER NOT NULL",
        "current_step": "INTEGER DEFAULT 0",
        "is_completed": "BOOLEAN DEFAULT FALSE",
        "xp_earned": "INTEGER DEFAULT 0",
        "correct_count": "INTEGER DEFAULT 0",
        "attempt_count": "INTEGER DEFAULT 0",
        "completed_at": "TIMESTAMP",
        "UNIQUE": "(user_id, lesson_id)",
        "FOREIGN KEY(user_id)": "REFERENCES users(id) ON DELETE CASCADE"
    })

    db.create_table("lesson_answers", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id": "INTEGER NOT NULL",
        "step_id": "INTEGER NOT NULL",
        "is_correct": "BOOLEAN NOT NULL",
        "submitted_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "FOREIGN KEY(user_id)": "REFERENCES users(id) ON DELETE CASCADE",
        "FOREIGN KEY(step_id)": "REFERENCES lesson_steps(id) ON DELETE CASCADE"
    })

    # Mastery is the memory that makes the next unit adaptive rather than random.
    db.create_table("skill_mastery", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id": "INTEGER NOT NULL",
        "skill_key": "TEXT NOT NULL",
        "skill_label": "TEXT",
        "subject": "TEXT",
        "attempts": "INTEGER DEFAULT 0",
        "correct": "INTEGER DEFAULT 0",
        "level": "INTEGER DEFAULT 0",
        "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "UNIQUE": "(user_id, skill_key)",
        "FOREIGN KEY(user_id)": "REFERENCES users(id) ON DELETE CASCADE"
    })

    # Wrong answers are re-served as targeted review in the next unit.
    db.create_table("mistake_bank", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id": "INTEGER NOT NULL",
        "skill_key": "TEXT",
        "skill_label": "TEXT",
        "question_text": "TEXT NOT NULL",
        "chosen_text": "TEXT",
        "correct_text": "TEXT",
        "explanation": "TEXT",
        "resolved": "BOOLEAN DEFAULT FALSE",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "FOREIGN KEY(user_id)": "REFERENCES users(id) ON DELETE CASCADE"
    })

    for table in ("sprint_questions", "quiz_questions"):
        db.add_column(table, "skill_key", "TEXT")
        db.add_column(table, "difficulty", "TEXT")

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
        'idx_sat_battles_status': 'sat_battles (status, created_at)',
        'idx_sat_battles_challenger': 'sat_battles (challenger_id, status)',
        'idx_sat_battles_opponent': 'sat_battles (opponent_id, status)',
        'idx_lesson_steps_lesson': 'lesson_steps (lesson_id, step_order)',
        'idx_skill_mastery_user': 'skill_mastery (user_id)',
        'idx_mistake_bank_user': 'mistake_bank (user_id, resolved, created_at DESC)',
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


def _get_gemini_client():
    """Load the Gemini SDK only when an AI feature is actually requested."""
    global gemini_client, gemini_types
    if not gemini_api_key:
        return None
    if gemini_client is None:
        from google import genai
        from google.genai import types as loaded_types
        gemini_types = loaded_types
        gemini_client = genai.Client(api_key=gemini_api_key)
    return gemini_client


def _gemini_config(max_output_tokens, *, system_instruction=None,
                   json_output=False, thinking_level="minimal"):
    """Return a conservative generation config tuned for latency and cost."""
    if _get_gemini_client() is None:
        raise RuntimeError("Gemini is not configured.")
    config = gemini_types.GenerateContentConfig(
        max_output_tokens=max_output_tokens,
        thinking_config=gemini_types.ThinkingConfig(thinking_level=thinking_level),
        system_instruction=system_instruction,
    )
    if json_output:
        config.response_mime_type = "application/json"
    return config


def _generate_text(prompt, *, max_output_tokens=800, json_output=False,
                   thinking_level="minimal", system_instruction=None):
    """Generate validated text through the single configured Gemini model."""
    client = _get_gemini_client()
    if client is None:
        raise RuntimeError("Gemini is not configured.")
    response = client.models.generate_content(
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


learning.configure(_generate_text, logger=app.logger)


# --- Skill mastery ---------------------------------------------------------
# Every graded answer anywhere in the product feeds one table, so the planner
# for the next unit sees a single honest picture of what the student can do.

def _record_skill_result(user_id, skill_key, skill_label, subject, is_correct):
    """Fold one graded answer into the student's mastery for that skill."""
    if not skill_key:
        return
    row = db.select_one("skill_mastery", where={"user_id": user_id, "skill_key": skill_key})
    attempts = (row["attempts"] if row else 0) + 1
    correct = (row["correct"] if row else 0) + (1 if is_correct else 0)
    level = learning.mastery_level(correct / attempts, attempts)
    payload = {
        "user_id": user_id,
        "skill_key": skill_key,
        "skill_label": skill_label or skill_key,
        "subject": subject or "",
        "attempts": attempts,
        "correct": correct,
        "level": level,
        "updated_at": datetime.now(ZoneInfo("UTC")).replace(tzinfo=None).isoformat(
            sep=" ", timespec="seconds"
        ),
    }
    if row:
        db.update("skill_mastery", payload, where={"id": row["id"]})
    else:
        db.insert("skill_mastery", payload)


def _record_mistake(user_id, skill_key, skill_label, question, chosen_text, correct_text, explanation):
    """Keep a wrong answer so the next unit can teach against it specifically."""
    db.insert("mistake_bank", {
        "user_id": user_id,
        "skill_key": skill_key or "",
        "skill_label": skill_label or "",
        "question_text": str(question or "")[:900],
        "chosen_text": str(chosen_text or "")[:400],
        "correct_text": str(correct_text or "")[:400],
        "explanation": str(explanation or "")[:900],
    })


def _get_mastery_rows(user_id):
    rows = db.select("skill_mastery", where={"user_id": user_id}) or []
    summary = []
    for row in rows:
        attempts = row["attempts"] or 0
        summary.append({
            "skill_key": row["skill_key"],
            "skill_label": row["skill_label"],
            "subject": row["subject"],
            "attempts": attempts,
            "correct": row["correct"] or 0,
            "accuracy": (row["correct"] or 0) / attempts if attempts else 0.0,
            "level": row["level"] or 0,
        })
    return summary


def _get_recent_mistakes_for_prompt(user_id, limit=8):
    rows = db.execute(
        """SELECT skill_label, question_text, chosen_text, correct_text, explanation
           FROM mistake_bank
           WHERE user_id=? AND resolved=False
           ORDER BY created_at DESC LIMIT ?""",
        (user_id, limit),
    ) or []
    if not rows:
        return "No graded mistakes recorded yet."
    lines = []
    for row in rows:
        lines.append(
            f"- [{row.get('skill_label') or 'general'}] {str(row.get('question_text') or '')[:220]}\n"
            f"  chose: {str(row.get('chosen_text') or '')[:120]} | correct: {str(row.get('correct_text') or '')[:120]}"
        )
    return "\n".join(lines)


def _award_xp(user_id, amount):
    """Add XP to the existing gamification counter and return the new total."""
    if amount <= 0:
        return None
    row = db.select_one("gamification_stats", where={"user_id": user_id})
    if not row:
        db.insert("gamification_stats", {"user_id": user_id, "points": amount, "current_streak": 0})
        return amount
    total = (row["points"] or 0) + amount
    db.update("gamification_stats", {"points": total}, where={"user_id": user_id})
    return total


def _advance_completion_streak(user_id):
    """Advance a student's streak once for a newly completed path step."""
    row = db.select_one("gamification_stats", where={"user_id": user_id})
    if not row:
        db.insert("gamification_stats", {
            "user_id": user_id, "points": 0, "current_streak": 0,
        })
        row = db.select_one("gamification_stats", where={"user_id": user_id})

    today = date.today()
    yesterday = today - timedelta(days=1)
    last_completed = None
    if row.get("last_completed_date"):
        try:
            last_completed = date.fromisoformat(row["last_completed_date"])
        except (TypeError, ValueError):
            app.logger.warning(
                "Resetting invalid completion date for user %s", user_id,
            )

    streak = row.get("current_streak") or 0
    if last_completed == today:
        next_streak = streak
    elif last_completed == yesterday:
        next_streak = streak + 1
    else:
        next_streak = 1

    db.update("gamification_stats", {
        "current_streak": next_streak,
        "last_completed_date": today.isoformat(),
    }, where={"user_id": user_id})


def _record_task_completion(user_id, task):
    """Claim a completion once, then record its activity and streak effects."""
    claimed = db.execute_write(
        "UPDATE paths SET is_completed=?, is_skipped=? "
        "WHERE id=? AND user_id=? AND is_completed=?",
        (True, False, task["id"], user_id, False),
    )
    if not claimed:
        return False
    log_activity(user_id, "task_completed", {
        "description": task["description"], "category": task["category"],
    })
    _advance_completion_streak(user_id)
    return True


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
    client = _get_gemini_client()
    if client is None:
        raise RuntimeError("Gemini is not configured.")
    gemini_history = _compact_chat_history(history)
    if not gemini_history:
        last_user_message = "Hello"
        prior_history = []
    else:
        last_user_message = gemini_history[-1]["parts"][0]["text"]
        prior_history = gemini_history[:-1]

    chat = client.chats.create(
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


def _task_fingerprint(description):
    """Return the meaningful words in a task for duplicate detection."""
    plain = re.sub(r"\[[^\]]+\]\([^)]+\)", " ", str(description or "").lower())
    words = re.findall(r"[a-z0-9]{3,}", plain)
    ignored = {
        "about", "after", "and", "complete", "digital", "guide", "lesson",
        "official", "practice", "review", "sat", "step", "strategy", "task",
        "test", "the", "then", "this", "using", "with", "write", "your",
    }
    return frozenset(word for word in words if word not in ignored)


def _is_duplicate_task(description, fingerprints):
    fingerprint = _task_fingerprint(description)
    if not fingerprint:
        return True
    for existing in fingerprints:
        overlap = len(fingerprint & existing)
        if overlap == len(fingerprint) == len(existing):
            return True
        if overlap >= 3 and overlap / max(len(fingerprint | existing), 1) >= 0.6:
            return True
    return False


def _repair_legacy_active_path(user_id, category):
    """Hide surplus AI-generated steps left by older path-builder versions.

    Personal steps remain active. Historical AI rows are retained for progress
    history, but only the first five generated steps form the live roadmap.
    """
    generated = db.select(
        "paths",
        where={
            "user_id": user_id,
            "category": category,
            "is_active": True,
            "is_user_added": False,
        },
        order_by="task_order ASC",
    )
    if len(generated) <= 5:
        return
    with db.transaction() as transaction:
        for task in generated[5:]:
            transaction.update("paths", {"is_active": False}, where={"id": task["id"]})
    app.logger.warning(
        "Deactivated %s surplus legacy path steps for user %s (%s)",
        len(generated) - 5, user_id, category,
    )


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


def _get_official_questions_for_topic(test_type, subject, topic, limit=10):
    """Fetch official questions from the official_questions table for a specific topic."""
    query = """
        SELECT id, question_text, options, correct_option, explanation, source_or_prompt, source_url
        FROM official_questions
        WHERE test_type = ? AND subject = ? AND topic LIKE ?
        ORDER BY RANDOM()
        LIMIT ?
    """
    questions = db.execute(query, (test_type, subject, f"%{topic}%", limit))
    if not questions:
        return []
    return [
        {
            "id": q['id'],
            "question_text": q['question_text'],
            "options": json.loads(q['options']) if isinstance(q['options'], str) else q['options'],
            "correct_option": q['correct_option'],
            "explanation": q['explanation'],
            "source_or_prompt": q['source_or_prompt'],
            "source_url": q['source_url'],
            "is_official": True
        }
        for q in questions
    ]


def _extract_official_examples_for_ai(test_type, subject, topic, count=3):
    """Fetch a few official questions to use as examples for AI generation."""
    questions = _get_official_questions_for_topic(test_type, subject, topic, limit=count)
    if not questions:
        return "No official examples available for this topic yet."
    
    examples = []
    for q in questions:
        examples.append(
            f"**Example Question:** {q['question_text']}\n"
            f"Options: {', '.join(q['options'])}\n"
            f"Correct: {q['options'][q['correct_option']]}\n"
            f"Explanation: {q['explanation']}\n"
        )
    return "\n---\n".join(examples)


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
@rate_limit('40/hour', name='practice_sprint')
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
        "source_or_prompt": q.get('source_or_prompt'),
        "question_text": q['question_text'],
        "options": json.loads(q['options']),
        "correct_option": q.get('correct_option', 0),
        "explanation": q.get('explanation', '')
    } for q in questions_raw]

    return jsonify({"title": sprint_details['title'], "questions": questions})


@app.route('/api/submit_sprint_results', methods=['POST'])
@login_required
@rate_limit('60/hour', name='sprint_results')
def submit_sprint_results(user):
    data = request.get_json(silent=True) or {}
    try:
        score = _score_assessment_results(user.data['id'], data.get('results'), 'sprint')
        return jsonify(score)
    except ValueError as error:
        return jsonify({"success": False, "error": str(error)}), 400


_ASSESSMENT_SOURCES = {
    'quiz': (
        """SELECT qq.id, qq.correct_option, qq.options, qq.explanation, qq.question_text,
                  qq.skill_key, p.id AS task_id, p.category, p.task_order,
                  p.skill_label, p.subject, p.xp_reward
           FROM quiz_questions qq
           JOIN quizzes q ON q.id=qq.quiz_id
           JOIN paths p ON p.id=q.task_id
           WHERE qq.id=? AND p.user_id=? AND p.is_active=True""",
        'quiz_results',
    ),
    'sprint': (
        """SELECT sq.id, sq.correct_option, sq.options, sq.explanation, sq.question_text,
                  sq.skill_key, p.id AS task_id, p.category, p.task_order,
                  p.skill_label, p.subject, p.xp_reward
           FROM sprint_questions sq
           JOIN practice_sprints ps ON ps.id=sq.sprint_id
           JOIN paths p ON p.id=ps.task_id
           WHERE sq.id=? AND p.user_id=? AND p.is_active=True""",
        'sprint_results',
    ),
}


def _grade_one_answer(user_id, question, selected_option, result_table):
    """Grade a single answer, persist it, and fold the first attempt into mastery."""
    options = json.loads(question['options'])
    if not 0 <= selected_option < len(options):
        raise ValueError("The selected option is not valid for this question.")
    correct_option = int(question['correct_option'])
    is_correct = selected_option == correct_option

    # Missed questions are deliberately re-served later in the run, and a step can
    # be replayed. Only the first attempt at a question counts toward mastery,
    # otherwise grinding one item to a correct answer would read as competence.
    prior_attempt_query = {
        'quiz_results': "SELECT id FROM quiz_results WHERE user_id=? AND question_id=? LIMIT 1",
        'sprint_results': "SELECT id FROM sprint_results WHERE user_id=? AND question_id=? LIMIT 1",
    }[result_table]
    first_attempt = not db.execute_for_one(prior_attempt_query, (user_id, question['id']))

    db.insert(result_table, {
        'user_id': user_id, 'question_id': question['id'], 'is_correct': is_correct
    })
    if not first_attempt:
        return {
            'question_id': question['id'], 'is_correct': is_correct,
            'correct_option': correct_option,
            'explanation': question.get('explanation') or '',
        }
    # A cumulative review mixes skills, so credit the question's own skill rather
    # than the step's headline skill.
    skill_key = question.get('skill_key') or ''
    if skill_key:
        resolved = learning.resolve_skill(skill_key)
        skill_label, subject = resolved['skill_label'], resolved['subject']
    else:
        skill_key = question.get('skill_key')
        skill_label, subject = question.get('skill_label'), question.get('subject')

    _record_skill_result(user_id, skill_key, skill_label, subject, is_correct)
    if not is_correct:
        _record_mistake(
            user_id, skill_key, skill_label,
            question.get('question_text'), options[selected_option],
            options[correct_option], question.get('explanation'),
        )
    return {
        'question_id': question['id'], 'is_correct': is_correct,
        'correct_option': correct_option,
        'explanation': question.get('explanation') or '',
    }


def _score_assessment_results(user_id, submitted, kind):
    if not isinstance(submitted, list) or not 1 <= len(submitted) <= 50:
        raise ValueError("Submit between 1 and 50 answers.")
    query, result_table = _ASSESSMENT_SOURCES['quiz' if kind == 'quiz' else 'sprint']
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
        scored.append(_grade_one_answer(user_id, question, selected_option, result_table))
    return {
        'success': True, 'correct': sum(1 for row in scored if row['is_correct']),
        'total': len(scored), 'results': scored,
    }


@app.route('/api/assessment/answer', methods=['POST'])
@login_required
@rate_limit('400/hour', name='assessment_answer')
def assessment_answer(user):
    """Grade one answer so the player can give Duolingo-style instant feedback."""
    data = request.get_json(silent=True) or {}
    kind = 'quiz' if data.get('kind') == 'quiz' else 'sprint'
    try:
        question_id = int(data.get('question_id'))
        selected_option = int(data.get('selected_option'))
    except (TypeError, ValueError):
        return jsonify({"error": "A question and an option are required."}), 400

    query, result_table = _ASSESSMENT_SOURCES[kind]
    question = db.execute_for_one(query, (question_id, user.data['id']))
    if not question:
        return jsonify({"error": "That question is not part of your active path."}), 404
    if _has_incomplete_earlier_task(user.data['id'], question):
        return jsonify({"error": "Complete the earlier path step first."}), 409
    try:
        return jsonify(_grade_one_answer(user.data['id'], question, selected_option, result_table))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@app.route('/api/assessment/finish', methods=['POST'])
@login_required
@rate_limit('60/hour', name='assessment_finish')
def assessment_finish(user):
    """Award XP from the answers actually recorded on the server for this step."""
    user_id = user.data['id']
    data = request.get_json(silent=True) or {}
    try:
        task_id = int(data.get('task_id'))
    except (TypeError, ValueError):
        return jsonify({"error": "A task is required."}), 400

    task = db.select_one("paths", where={"id": task_id, "user_id": user_id, "is_active": True})
    if not task:
        return jsonify({"error": "That step is not part of your active path."}), 404
    if task.get('task_format') not in {'quiz', 'practice_sprint'}:
        return jsonify({"error": "That step is not a scored practice activity."}), 400
    if _has_incomplete_earlier_task(user_id, task):
        return jsonify({"error": "Complete the earlier path step first."}), 409

    # Scored on first attempts only: missed questions are re-served during the
    # run, so counting every attempt would let a replay inflate the result.
    if task.get('task_format') == 'quiz':
        summary = db.execute_for_one(
            """SELECT COUNT(*) AS total, SUM(CASE WHEN r.is_correct THEN 1 ELSE 0 END) AS correct
               FROM quiz_results r
               WHERE r.id IN (
                   SELECT MIN(r2.id) FROM quiz_results r2
                   JOIN quiz_questions qq ON qq.id=r2.question_id
                   JOIN quizzes q ON q.id=qq.quiz_id
                   WHERE q.task_id=? AND r2.user_id=?
                   GROUP BY r2.question_id)""",
            (task_id, user_id),
        )
        expected = db.execute_for_one(
            """SELECT COUNT(*) AS total FROM quiz_questions qq
               JOIN quizzes q ON q.id=qq.quiz_id WHERE q.task_id=?""",
            (task_id,),
        )
    else:
        summary = db.execute_for_one(
            """SELECT COUNT(*) AS total, SUM(CASE WHEN r.is_correct THEN 1 ELSE 0 END) AS correct
               FROM sprint_results r
               WHERE r.id IN (
                   SELECT MIN(r2.id) FROM sprint_results r2
                   JOIN sprint_questions sq ON sq.id=r2.question_id
                   JOIN practice_sprints ps ON ps.id=sq.sprint_id
                   WHERE ps.task_id=? AND r2.user_id=?
                   GROUP BY r2.question_id)""",
            (task_id, user_id),
        )
        expected = db.execute_for_one(
            """SELECT COUNT(*) AS total FROM sprint_questions sq
               JOIN practice_sprints ps ON ps.id=sq.sprint_id WHERE ps.task_id=?""",
            (task_id,),
        )

    total = (summary or {}).get('total') or 0
    expected_total = (expected or {}).get('total') or 0
    if expected_total <= 0 or total < expected_total:
        return jsonify({"error": "Finish every question before completing this step."}), 409
    correct = (summary or {}).get('correct') or 0
    accuracy = correct / total if total else 0.0
    base = task.get('xp_reward') or 20
    earned = int(round(base * (0.5 + 0.5 * accuracy))) if total else 0

    # Only the improvement over what this step already paid out is granted, so
    # re-running a drill (or replaying this call) cannot farm points.
    already = task.get('xp_awarded') or 0
    xp_delta = max(0, earned - already)
    if xp_delta:
        db.execute_write(
            "UPDATE paths SET xp_awarded=? WHERE id=? AND user_id=?",
            (earned, task_id, user_id),
        )
    completed_now = _record_task_completion(user_id, task)
    return jsonify({
        "xp_earned": xp_delta,
        "total_points": _award_xp(user_id, xp_delta) if xp_delta else None,
        "accuracy": round(accuracy, 3),
        "completed": completed_now or bool(task.get('is_completed')),
    })


# --- Lesson player ---------------------------------------------------------

def _load_lesson_for_task(user_id, task_id):
    """Return (task, lesson) for a lesson step the user is allowed to open."""
    task = db.select_one("paths", where={"id": task_id, "user_id": user_id, "is_active": True})
    if not task:
        return None, None, ("That step is not part of your active path.", 404)
    if task.get('task_format') != 'lesson':
        return None, None, ("That step is not a lesson.", 404)
    if _has_incomplete_earlier_task(user_id, task):
        return None, None, ("Complete the earlier path step first.", 409)
    lesson = db.select_one("lessons", where={"task_id": task_id})
    if not lesson:
        return None, None, ("This lesson has no content yet.", 404)
    return task, lesson, None


@app.route('/api/lesson/<int:task_id>')
@login_required
@rate_limit('120/hour', name='lesson_fetch')
def get_lesson(user, task_id):
    user_id = user.data['id']
    task, lesson, error = _load_lesson_for_task(user_id, task_id)
    if error:
        return jsonify({"error": error[0]}), error[1]

    steps_raw = db.select("lesson_steps", where={"lesson_id": lesson['id']}, order_by="step_order ASC")
    steps = []
    for step in sorted(steps_raw, key=lambda s: s['step_order']):
        payload = {
            "id": step['id'],
            "step_type": step['step_type'],
            "title": step.get('title') or "",
        }
        if step['step_type'] == 'check':
            payload.update({
                "source_or_prompt": step.get('source_or_prompt') or "",
                "question_text": step.get('question_text') or "",
                "options": json.loads(step['options']) if step.get('options') else [],
            })
        else:
            payload.update({
                "body": step.get('body') or "",
                "worked_example": step.get('worked_example') or "",
                "takeaway": step.get('takeaway') or "",
                "trap": step.get('trap') or "",
            })
        steps.append(payload)

    progress = db.select_one("lesson_progress", where={"user_id": user_id, "lesson_id": lesson['id']})
    return jsonify({
        "task_id": task_id,
        "lesson_id": lesson['id'],
        "title": lesson['title'],
        "skill_label": lesson.get('skill_label') or "",
        "subject": lesson.get('subject') or "",
        "objective": lesson.get('objective') or "",
        "intro": lesson.get('intro') or "",
        "recap": lesson.get('recap') or "",
        "xp_reward": lesson.get('xp_reward') or 30,
        "steps": steps,
        "progress": {
            "current_step": (progress or {}).get('current_step') or 0,
            "is_completed": bool((progress or {}).get('is_completed')),
        },
    })


@app.route('/api/lesson/<int:task_id>/answer', methods=['POST'])
@login_required
@rate_limit('400/hour', name='lesson_answer')
def lesson_answer(user, task_id):
    """Grade one in-lesson check and return the teaching explanation with it."""
    user_id = user.data['id']
    task, lesson, error = _load_lesson_for_task(user_id, task_id)
    if error:
        return jsonify({"error": error[0]}), error[1]
    data = request.get_json(silent=True) or {}
    try:
        step_id = int(data.get('step_id'))
        selected_option = int(data.get('selected_option'))
    except (TypeError, ValueError):
        return jsonify({"error": "A step and an option are required."}), 400

    step = db.select_one("lesson_steps", where={"id": step_id, "lesson_id": lesson['id']})
    if not step or step['step_type'] != 'check':
        return jsonify({"error": "That question is not part of this lesson."}), 404

    options = json.loads(step['options']) if step.get('options') else []
    if not 0 <= selected_option < len(options):
        return jsonify({"error": "That option is not valid for this question."}), 400

    correct_option = int(step['correct_option'] or 0)
    is_correct = selected_option == correct_option

    # As with drills, a repeated attempt at the same check is for learning, not
    # for measurement, so only the first one moves mastery.
    first_attempt = not db.execute_for_one(
        "SELECT id FROM lesson_answers WHERE user_id=? AND step_id=? LIMIT 1",
        (user_id, step_id),
    )
    db.insert("lesson_answers", {
        "user_id": user_id, "step_id": step_id, "is_correct": is_correct,
    })
    if first_attempt:
        _record_skill_result(
            user_id, lesson.get('skill_key'), lesson.get('skill_label'),
            lesson.get('subject'), is_correct,
        )
        if not is_correct:
            _record_mistake(
                user_id, lesson.get('skill_key'), lesson.get('skill_label'),
                step.get('question_text'), options[selected_option],
                options[correct_option], step.get('explanation'),
            )

    progress = db.select_one("lesson_progress", where={"user_id": user_id, "lesson_id": lesson['id']})
    if progress:
        db.update("lesson_progress", {
            "attempt_count": (progress['attempt_count'] or 0) + 1,
            "correct_count": (progress['correct_count'] or 0) + (1 if is_correct else 0),
        }, where={"id": progress['id']})
    else:
        db.insert("lesson_progress", {
            "user_id": user_id, "lesson_id": lesson['id'], "current_step": 0,
            "attempt_count": 1, "correct_count": 1 if is_correct else 0,
        })

    return jsonify({
        "is_correct": is_correct,
        "correct_option": correct_option,
        "explanation": step.get('explanation') or "",
    })


@app.route('/api/lesson/<int:task_id>/progress', methods=['POST'])
@login_required
@rate_limit('400/hour', name='lesson_progress')
def lesson_progress(user, task_id):
    """Remember how far into a lesson the student got, so they can resume."""
    user_id = user.data['id']
    task, lesson, error = _load_lesson_for_task(user_id, task_id)
    if error:
        return jsonify({"error": error[0]}), error[1]
    data = request.get_json(silent=True) or {}
    try:
        current_step = max(0, min(200, int(data.get('current_step', 0))))
    except (TypeError, ValueError):
        return jsonify({"error": "A step index is required."}), 400

    existing = db.select_one("lesson_progress", where={"user_id": user_id, "lesson_id": lesson['id']})
    if existing:
        db.update("lesson_progress", {"current_step": current_step}, where={"id": existing['id']})
    else:
        db.insert("lesson_progress", {
            "user_id": user_id, "lesson_id": lesson['id'], "current_step": current_step,
        })
    return jsonify({"success": True, "current_step": current_step})


# --- Boss battle: logging a real official practice test -------------------
# A boss battle is the only step whose work happens outside Mentics, so the
# score is the only evidence it produced anything. Section scores are captured
# rather than a bare total: the total alone cannot tell the planner which half
# of the test moved, and it never reaches the stats page.

TEST_SECTIONS = {
    'SAT': [
        ('sat_ebrw', 'Reading & Writing', 200, 800),
        ('sat_math', 'Math', 200, 800),
    ],
    'ACT': [
        ('act_math', 'Math', 1, 36),
        ('act_reading', 'Reading', 1, 36),
        ('act_science', 'Science', 1, 36),
    ],
}


def _boss_battle_test_type(task):
    label = f"{task.get('description') or ''} {task.get('stat_to_update') or ''}".lower()
    return 'ACT' if 'act' in label and 'sat' not in label else 'SAT'


@app.route('/api/boss_battle/<int:task_id>', methods=['GET'])
@login_required
@rate_limit('120/hour', name='boss_battle_detail')
def boss_battle_detail(user, task_id):
    """Describe the score fields this boss battle expects."""
    user_id = user.data['id']
    task = db.select_one("paths", where={"id": task_id, "user_id": user_id, "is_active": True})
    if not task:
        return jsonify({"error": "That step is not part of your active path."}), 404
    if _has_incomplete_earlier_task(user_id, task):
        return jsonify({"error": "Complete the earlier path step first."}), 409

    test_type = _boss_battle_test_type(task)
    stats = user.get_stats()
    sections = []
    for key, label, minimum, maximum in TEST_SECTIONS[test_type]:
        sections.append({
            "key": key, "label": label, "min": minimum, "max": maximum,
            "previous": stats.get(key) or None,
        })
    return jsonify({
        "task_id": task_id, "test_type": test_type, "sections": sections,
        "is_completed": bool(task.get('is_completed')),
    })


@app.route('/api/boss_battle/<int:task_id>/result', methods=['POST'])
@login_required
@rate_limit('20/hour', name='boss_battle_result')
def boss_battle_result(user, task_id):
    """Record a full official practice test, then close out the step."""
    user_id = user.data['id']
    task = db.select_one("paths", where={"id": task_id, "user_id": user_id, "is_active": True})
    if not task:
        return jsonify({"error": "That step is not part of your active path."}), 404
    if _has_incomplete_earlier_task(user_id, task):
        return jsonify({"error": "Complete the earlier path step first."}), 409

    test_type = _boss_battle_test_type(task)
    submitted = (request.get_json(silent=True) or {}).get('scores') or {}
    if not isinstance(submitted, dict):
        return jsonify({"error": "Scores must be provided per section."}), 400

    stats = user.get_stats()
    # A student who has not logged a test here still gave a baseline in the path
    # builder. Without this fallback their first boss battle reports no change
    # even though the starting score is known.
    baseline = stats.get("test_path") or {}
    previous = {}
    recorded = {}
    for key, label, minimum, maximum in TEST_SECTIONS[test_type]:
        raw = submitted.get(key)
        if raw is None or str(raw).strip() == "":
            return jsonify({"error": f"Enter your {label} score to log this test."}), 400
        try:
            value = int(float(raw))
        except (TypeError, ValueError):
            return jsonify({"error": f"{label} must be a number."}), 400
        if not minimum <= value <= maximum:
            return jsonify({"error": f"{label} must be between {minimum} and {maximum}."}), 400
        previous[key] = stats.get(key) or baseline.get(f"current_{key}")
        recorded[key] = value

    # Section scores drive the stats page, so they are written to the profile as
    # well as to history. The composite is derived, never entered by hand.
    for key, value in recorded.items():
        stats[key] = value
        db.insert("stat_history", {
            "user_id": user_id, "stat_name": key, "stat_value": value,
        })
    user.set_stats(stats)

    if test_type == 'SAT':
        composite_key, composite = 'sat_total', sum(recorded.values())
        previous_composite = None
        if all(previous.get(k) for k in recorded):
            try:
                previous_composite = sum(int(previous[k]) for k in recorded)
            except (TypeError, ValueError):
                previous_composite = None
    else:
        composite_key = 'act_composite'
        composite = round(sum(recorded.values()) / len(recorded))
        previous_composite = None
        prior = [previous.get(k) for k in recorded]
        if all(prior):
            try:
                previous_composite = round(sum(int(v) for v in prior) / len(prior))
            except (TypeError, ValueError):
                previous_composite = None

    db.insert("stat_history", {
        "user_id": user_id, "stat_name": composite_key, "stat_value": composite,
    })
    log_activity(user_id, 'test_logged', {
        'test_type': test_type, 'composite': composite, 'sections': recorded,
    })

    newly_completed = _record_task_completion(user_id, task)
    xp = 0
    if newly_completed:
        xp = task.get('xp_reward') or 100
        _award_xp(user_id, xp)

    return jsonify({
        "success": True,
        "test_type": test_type,
        "composite": composite,
        "composite_label": 'Total' if test_type == 'SAT' else 'Composite',
        "previous_composite": previous_composite,
        "delta": (composite - previous_composite) if previous_composite is not None else None,
        "sections": recorded,
        "xp_earned": xp,
    })


# --- College milestone: logging a real deliverable -------------------------
# The college equivalent of a boss battle. The work happens outside Mentics, so
# the recorded number is the evidence, and it is what the next unit builds on.

MILESTONE_FIELDS = {
    'colleges_researched': ("How many colleges are on your list now?", "colleges", 0, 1000),
    'applications_submitted': ("How many applications have you submitted?", "applications", 0, 1000),
    'essay_progress': ("Where is your personal statement?", "stage", 1, 2),
}


@app.route('/api/milestone/<int:task_id>', methods=['GET'])
@login_required
@rate_limit('120/hour', name='milestone_detail')
def milestone_detail(user, task_id):
    user_id = user.data['id']
    task = db.select_one("paths", where={"id": task_id, "user_id": user_id, "is_active": True})
    if not task or task.get('task_format') != 'milestone':
        return jsonify({"error": "That step is not a milestone."}), 404
    if _has_incomplete_earlier_task(user_id, task):
        return jsonify({"error": "Complete the earlier path step first."}), 409

    stat = task.get('stat_to_update')
    field = MILESTONE_FIELDS.get(stat)
    stats = user.get_stats()
    return jsonify({
        "task_id": task_id,
        "objective": task.get('objective') or task.get('description'),
        "stat_name": stat if field else None,
        "label": field[0] if field else None,
        "unit": field[1] if field else None,
        "min": field[2] if field else None,
        "max": field[3] if field else None,
        "previous": stats.get(stat) if field else None,
        "is_completed": bool(task.get('is_completed')),
    })


@app.route('/api/milestone/<int:task_id>/result', methods=['POST'])
@login_required
@rate_limit('30/hour', name='milestone_result')
def milestone_result(user, task_id):
    user_id = user.data['id']
    task = db.select_one("paths", where={"id": task_id, "user_id": user_id, "is_active": True})
    if not task or task.get('task_format') != 'milestone':
        return jsonify({"error": "That step is not a milestone."}), 404
    if _has_incomplete_earlier_task(user_id, task):
        return jsonify({"error": "Complete the earlier path step first."}), 409

    stat = task.get('stat_to_update')
    field = MILESTONE_FIELDS.get(stat)
    previous = None
    value = None
    if field:
        raw = (request.get_json(silent=True) or {}).get('value')
        if raw is None or str(raw).strip() == "":
            return jsonify({"error": f"Enter a number to finish this step."}), 400
        try:
            value = int(float(raw))
        except (TypeError, ValueError):
            return jsonify({"error": "That needs to be a number."}), 400
        if not field[2] <= value <= field[3]:
            return jsonify({"error": f"Enter a value between {field[2]} and {field[3]}."}), 400

        stats = user.get_stats()
        previous = stats.get(stat)
        stats[stat] = value
        user.set_stats(stats)
        db.insert("stat_history", {
            "user_id": user_id, "stat_name": stat, "stat_value": value,
        })
        log_activity(user_id, 'milestone_logged', {'stat_name': stat, 'stat_value': value})

    newly_completed = _record_task_completion(user_id, task)
    xp = 0
    if newly_completed:
        xp = task.get('xp_reward') or 90
        _award_xp(user_id, xp)

    try:
        delta = int(value) - int(previous) if value is not None and previous not in (None, "") else None
    except (TypeError, ValueError):
        delta = None
    return jsonify({
        "success": True, "value": value, "previous": previous, "delta": delta,
        "unit": field[1] if field else None, "xp_earned": xp,
    })


@app.route('/api/lesson/<int:task_id>/finish', methods=['POST'])
@login_required
@rate_limit('60/hour', name='lesson_finish')
def lesson_finish(user, task_id):
    """Close out a lesson: award XP scaled by how the in-lesson checks went."""
    user_id = user.data['id']
    task, lesson, error = _load_lesson_for_task(user_id, task_id)
    if error:
        return jsonify({"error": error[0]}), error[1]

    summary = db.execute_for_one(
        """SELECT COUNT(*) AS total, SUM(CASE WHEN la.is_correct THEN 1 ELSE 0 END) AS correct
           FROM lesson_answers la
           WHERE la.id IN (
               SELECT MIN(a2.id) FROM lesson_answers a2
               JOIN lesson_steps ls ON ls.id=a2.step_id
               WHERE ls.lesson_id=? AND a2.user_id=?
               GROUP BY a2.step_id)""",
        (lesson['id'], user_id),
    ) or {}
    total = summary.get('total') or 0
    correct = summary.get('correct') or 0
    expected = db.execute_for_one(
        "SELECT COUNT(*) AS total FROM lesson_steps WHERE lesson_id=? AND step_type='check'",
        (lesson['id'],),
    ) or {}
    if total < (expected.get('total') or 0):
        return jsonify({"error": "Finish every check before completing this lesson."}), 409
    accuracy = correct / total if total else 1.0

    progress = db.select_one("lesson_progress", where={"user_id": user_id, "lesson_id": lesson['id']})
    already_awarded = (progress or {}).get('xp_earned') or 0
    base = lesson.get('xp_reward') or 30
    earned = int(round(base * (0.6 + 0.4 * accuracy)))
    xp_delta = max(0, earned - already_awarded)

    payload = {
        "is_completed": True,
        "xp_earned": max(earned, already_awarded),
        "completed_at": datetime.now(ZoneInfo("UTC")).replace(tzinfo=None).isoformat(
            sep=" ", timespec="seconds"
        ),
    }
    if progress:
        db.update("lesson_progress", payload, where={"id": progress['id']})
    else:
        db.insert("lesson_progress", {
            "user_id": user_id, "lesson_id": lesson['id'], "current_step": 0,
            "correct_count": correct, "attempt_count": total, **payload,
        })

    current_path_xp = task.get('xp_awarded') or 0
    if earned > current_path_xp:
        db.execute_write(
            "UPDATE paths SET xp_awarded=? WHERE id=? AND user_id=?",
            (earned, task_id, user_id),
        )
    completed_now = _record_task_completion(user_id, task)

    return jsonify({
        "success": True,
        "correct": correct,
        "total": total,
        "xp_earned": xp_delta,
        "total_points": _award_xp(user_id, xp_delta) if xp_delta else None,
        "recap": lesson.get('recap') or "",
        "completed": completed_now or bool(task.get('is_completed')),
    })


# --- In-context AI coach ---------------------------------------------------

_COACH_SYSTEM = (
    "You are the Mentics tutor helping a student who is in the middle of a lesson or practice "
    "question right now. You can see exactly what they are looking at. Explain the specific thing "
    "in front of them, using their own question and answer choices. Be concrete: name the rule, "
    "show the step, point at the words or numbers that decide it. Never tell them to go read "
    "something else. Under 180 words. Plain markdown, no headings. Warm and direct."
)

_COACH_HINT_SYSTEM = (
    "You are the Mentics tutor. The student is looking at a question they have NOT answered yet, "
    "so you must NOT tell them which choice is correct and must not eliminate choices for them. "
    "Give one nudge: name what the question is really testing and the first move to make. Ask them "
    "a question back that points at the deciding detail. Under 120 words. Plain markdown, no "
    "headings. Encouraging and specific."
)


@app.route('/api/coach', methods=['POST'])
@login_required
@rate_limit('80/hour', name='coach')
def coach(user):
    """Answer a question about the exact lesson step or item on the student's screen.

    This is what connects the path to the Mentics chatbot: the student never has
    to re-explain their context, because the server looks it up by id.
    """
    user_id = user.data['id']
    data = request.get_json(silent=True) or {}
    kind = data.get('kind')
    message = str(data.get('message') or '').strip()[:600]
    try:
        ref_id = int(data.get('ref_id'))
    except (TypeError, ValueError):
        return jsonify({"error": "A reference is required."}), 400

    # A question the student has not attempted yet gets a hint, never the answer.
    # The player only offers the tutor after an attempt, but the endpoint must
    # hold that line on its own.
    context = ""
    answered = True
    if kind == 'lesson_step':
        step = db.execute_for_one(
            """SELECT ls.*, l.skill_label, l.subject FROM lesson_steps ls
               JOIN lessons l ON l.id=ls.lesson_id
               JOIN paths p ON p.id=l.task_id
               WHERE ls.id=? AND p.user_id=?""",
            (ref_id, user_id),
        )
        if not step:
            return jsonify({"error": "That lesson step is not yours."}), 404
        if step['step_type'] == 'check':
            options = json.loads(step['options']) if step.get('options') else []
            answered = bool(db.execute_for_one(
                "SELECT id FROM lesson_answers WHERE user_id=? AND step_id=? LIMIT 1",
                (user_id, ref_id),
            ))
            context = (
                f"Skill: {step.get('skill_label')} ({step.get('subject')})\n"
                f"Stimulus: {step.get('source_or_prompt') or 'none'}\n"
                f"Question: {step.get('question_text')}\n"
                f"Choices: {'; '.join(options)}\n"
            )
            if answered:
                context += (
                    f"Correct choice: {options[int(step['correct_option'] or 0)] if options else 'unknown'}\n"
                    f"Existing explanation: {step.get('explanation')}"
                )
        else:
            context = (
                f"Skill: {step.get('skill_label')} ({step.get('subject')})\n"
                f"Lesson card: {step.get('title')}\n"
                f"{step.get('body')}\n"
                f"Worked example: {step.get('worked_example')}"
            )
    elif kind in ('sprint', 'quiz'):
        query, result_table = _ASSESSMENT_SOURCES[kind]
        question = db.execute_for_one(query, (ref_id, user_id))
        if not question:
            return jsonify({"error": "That question is not yours."}), 404
        options = json.loads(question['options'])
        prior_query = {
            'quiz_results': "SELECT id FROM quiz_results WHERE user_id=? AND question_id=? LIMIT 1",
            'sprint_results': "SELECT id FROM sprint_results WHERE user_id=? AND question_id=? LIMIT 1",
        }[result_table]
        answered = bool(db.execute_for_one(prior_query, (user_id, ref_id)))
        context = (
            f"Skill: {question.get('skill_label')} ({question.get('subject')})\n"
            f"Stimulus: {question.get('source_or_prompt') or 'none'}\n"
            f"Question: {question.get('question_text')}\n"
            f"Choices: {'; '.join(options)}\n"
        )
        if answered:
            context += (
                f"Correct choice: {options[int(question['correct_option'])]}\n"
                f"Existing explanation: {question.get('explanation')}"
            )
    else:
        return jsonify({"error": "Unsupported coaching context."}), 400

    if not os.getenv("GEMINI_API_KEY"):
        return jsonify({"reply": "The Mentics tutor is offline right now, but the written explanation below covers this step."})

    prompt = (
        f"# WHAT THE STUDENT IS LOOKING AT\n{context}\n\n"
        f"# THEIR QUESTION\n{message or 'Explain this to me more clearly.'}\n\n"
        + ("Answer their question about this exact item."
           if answered else
           "They have not answered yet. Nudge them toward the reasoning without revealing "
           "which choice is correct.")
    )
    try:
        reply = _generate_text(
            prompt, max_output_tokens=600, thinking_level="minimal",
            system_instruction=_COACH_SYSTEM if answered else _COACH_HINT_SYSTEM,
        )
    except Exception:
        app.logger.exception("Coach reply failed for user %s", user_id)
        return jsonify({"error": "I couldn't reach the tutor just now. Try again in a moment."}), 502
    return jsonify({"reply": reply})


def _build_learner_profile(user_id, test_path_info, chat_history):
    """Assemble everything the lesson planner needs about one student."""
    test_focus = (test_path_info.get("test_focus") or "sat").lower()
    focus_label = {"act": "ACT", "both": "Digital SAT and ACT"}.get(test_focus, "Digital SAT")

    current = []
    for key, label in (
        ("current_sat_ebrw", "SAT Reading & Writing"), ("current_sat_math", "SAT Math"),
        ("current_act_composite", "ACT Composite"), ("current_act_math", "ACT Math"),
        ("current_act_reading", "ACT Reading"), ("current_act_science", "ACT Science"),
    ):
        if test_path_info.get(key):
            current.append(f"{label} {test_path_info[key]}")

    goals = []
    if test_path_info.get("desired_sat"):
        goals.append(f"SAT {test_path_info['desired_sat']}")
    if test_path_info.get("desired_act"):
        goals.append(f"ACT {test_path_info['desired_act']}")

    test_date_info = "Not set"
    if test_path_info.get("test_date"):
        try:
            user_tz = ZoneInfo(session.get('timezone', 'UTC'))
            test_date = datetime.strptime(test_path_info["test_date"], '%Y-%m-%d').date()
            days = (test_date - datetime.now(user_tz).date()).days
            test_date_info = f"{test_date.strftime('%B %d, %Y')} ({days} days away)" if days >= 0 \
                else f"{test_date.strftime('%B %d, %Y')} (already passed)"
        except (ValueError, ZoneInfoNotFoundError, KeyError):
            test_date_info = "Not set"

    mastery_rows = _get_mastery_rows(user_id)
    taught = db.execute(
        """SELECT DISTINCT skill_label FROM paths
           WHERE user_id=? AND category='Test Prep' AND node_type='lesson'
             AND is_completed=True AND skill_label IS NOT NULL LIMIT 15""",
        (user_id,),
    ) or []
    taught_labels = [row["skill_label"] for row in taught if row.get("skill_label")]

    latest_request = next(
        (m['content'] for m in reversed(chat_history or []) if m.get('role') == 'user'),
        "No specific request -- build the best next unit from the data.",
    )

    # A rough ability read so the teaching call pitches at the right level.
    scores = [int(test_path_info[k]) for k in ("current_sat_ebrw", "current_sat_math")
              if str(test_path_info.get(k) or "").isdigit()]
    if scores:
        average = sum(scores) / len(scores)
        level_hint = ("advanced -- already scoring high, so target the hardest question types"
                      if average >= 700 else
                      "solid mid-range -- knows the basics, loses points on multi-step and trap questions"
                      if average >= 550 else
                      "building fundamentals -- needs the underlying concept before test tactics")
    else:
        level_hint = "unknown baseline -- teach the fundamentals clearly before advanced tactics"

    return {
        "focus": test_focus,
        "focus_label": focus_label,
        "current_scores": ", ".join(current) or "Not provided",
        "goal_scores": ", ".join(goals) or "Not specified",
        "test_date": test_date_info,
        "hours_per_week": test_path_info.get("hours_per_week") or "Not specified",
        "strengths": test_path_info.get("strengths") or "None listed",
        "weaknesses": test_path_info.get("weaknesses") or "None listed",
        "mastery_summary": learning.format_mastery_summary(mastery_rows),
        "recent_mistakes": _get_recent_mistakes_for_prompt(user_id),
        "taught_skills": ", ".join(taught_labels) or "None yet",
        "latest_request": latest_request,
        "standing_focus": _describe_standing_focus(test_path_info),
        "chat_history": _format_chat_history_for_prompt(chat_history or []),
        "level_hint": level_hint,
        "skill_options": learning.skill_catalog(test_focus),
        "_mastery_rows": mastery_rows,
        "_completed_lessons": len(taught_labels),
    }


def _official_examples_for_skill(skill):
    """Give the question writer a few real official items to imitate."""
    test_type = "ACT" if skill.get("test") == "ACT" else "SAT"
    examples = _extract_official_examples_for_ai(
        test_type, skill["subject"], skill["skill_label"], count=2
    )
    if not examples or examples.startswith("No official examples"):
        return ""
    return f"# OFFICIAL QUESTIONS TO MATCH IN STYLE AND DIFFICULTY\n{examples}\n"


def _persist_unit(user_id, unit, category="Test Prep"):
    """Write a generated unit to the database as the student's active path."""
    saved = []
    with db.transaction() as transaction:
        transaction.update("paths", {"is_active": False}, where={
            "user_id": user_id, "category": category, "is_active": True,
            "is_user_added": False,
        })

        for index, node in enumerate(unit["nodes"]):
            skill = node["skill"]
            node_type = node["node_type"]
            task_format = {
                "lesson": "lesson", "practice_sprint": "practice_sprint",
                "quiz": "quiz", "boss_battle": "boss_battle",
                # A college unit ends in a real deliverable rather than a test.
                "milestone": "milestone",
            }[node_type]

            description = node["title"]
            if node_type == "boss_battle":
                description = (
                    f"Boss Battle: sit a full, timed official {node['test_name']} practice test on "
                    f"{node['platform']}, then log your score. [Official practice]({node['resource_url']})"
                )

            task_data = {
                "user_id": user_id, "task_order": index + 1,
                "description": description,
                "reason": node["reason"],
                "type": "milestone" if node_type in ("boss_battle", "milestone") else "standard",
                "stat_to_update": node.get("stat_to_update"),
                "category": category, "is_active": True, "is_completed": False,
                "task_format": task_format,
                "skill_key": skill["skill_key"], "skill_label": skill["skill_label"],
                "subject": skill["subject"], "node_type": node_type,
                "objective": node["objective"], "xp_reward": node["xp_reward"],
                "unit_title": unit["unit_title"],
            }
            task_id = transaction.insert("paths", task_data)

            if node_type == "lesson":
                lesson_id = transaction.insert("lessons", {
                    "task_id": task_id, "title": node["title"],
                    "skill_key": skill["skill_key"], "skill_label": skill["skill_label"],
                    "subject": skill["subject"], "objective": node["objective"],
                    "intro": node["teaching"].get("intro", ""),
                    "recap": node["teaching"].get("recap", ""),
                    "xp_reward": node["xp_reward"],
                })
                for order, step in enumerate(node["steps"]):
                    transaction.insert("lesson_steps", {
                        "lesson_id": lesson_id, "step_order": order,
                        "step_type": step["step_type"], "title": step.get("title", ""),
                        "body": step.get("body", ""),
                        "worked_example": step.get("worked_example", ""),
                        "takeaway": step.get("takeaway", ""), "trap": step.get("trap", ""),
                        "source_or_prompt": step.get("source_or_prompt", ""),
                        "question_text": step.get("question_text", ""),
                        "options": json.dumps(step.get("options")) if step.get("options") else None,
                        "correct_option": step.get("correct_option"),
                        "explanation": step.get("explanation", ""),
                    })
                transaction.update("paths", {"task_content_id": lesson_id}, where={"id": task_id})

            elif node_type == "practice_sprint":
                sprint_id = transaction.insert("practice_sprints", {
                    "task_id": task_id, "title": node["title"],
                })
                for question in node["questions"]:
                    transaction.insert("sprint_questions", {
                        "sprint_id": sprint_id,
                        "source_or_prompt": question["source_or_prompt"],
                        "question_text": question["question_text"],
                        "options": json.dumps(question["options"]),
                        "correct_option": question["correct_option"],
                        "explanation": question["explanation"],
                        "skill_key": question.get("skill_key") or skill["skill_key"],
                        "difficulty": question.get("difficulty", "medium"),
                    })
                transaction.update("paths", {"task_content_id": sprint_id}, where={"id": task_id})

            elif node_type == "quiz":
                quiz_id = transaction.insert("quizzes", {
                    "task_id": task_id, "title": node["title"],
                })
                for question in node["questions"]:
                    transaction.insert("quiz_questions", {
                        "quiz_id": quiz_id,
                        "source_or_prompt": question["source_or_prompt"],
                        "question_text": question["question_text"],
                        "options": json.dumps(question["options"]),
                        "correct_option": question["correct_option"],
                        "explanation": question["explanation"],
                        "skill_key": question.get("skill_key") or skill["skill_key"],
                        "difficulty": question.get("difficulty", "medium"),
                    })
                transaction.update("paths", {"task_content_id": quiz_id}, where={"id": task_id})

            saved.append({**task_data, "id": task_id})

        transaction.insert("activity_log", {
            "user_id": user_id, "activity_type": "path_generated",
            "details": json.dumps({"category": category, "unit": unit["unit_title"]}),
        })
    return saved


def _generate_and_save_new_test_path(user_id, test_path_info, chat_history=None):
    """Build the next adaptive unit: plan once, then generate every node's content.

    Content generation is fanned out across several small Gemini calls rather
    than one large one. A node whose content call fails is downgraded to a
    format that still works instead of poisoning the whole path.
    """
    profile = _build_learner_profile(user_id, test_path_info or {}, chat_history or [])
    shape = learning.choose_shape(profile["_mastery_rows"], profile["_completed_lessons"])

    unit = learning.build_unit(
        profile, shape=shape, official_examples_fn=_official_examples_for_skill,
    )

    # A drill node with no questions is worse than useless, so fall back to
    # whatever official questions exist before giving up on the node.
    for node in unit["nodes"]:
        if node["node_type"] in ("practice_sprint", "quiz") and not node.get("questions"):
            skill = node["skill"]
            test_type = "ACT" if skill.get("test") == "ACT" else "SAT"
            wanted = learning.EXERCISE_COUNT[node["node_type"]]
            official = _get_official_questions_for_topic(
                test_type, skill["subject"], skill["skill_label"], limit=wanted
            )
            node["questions"] = [{
                "source_or_prompt": q.get("source_or_prompt") or "Official practice question.",
                "question_text": q["question_text"], "options": q["options"],
                "correct_option": q["correct_option"],
                "explanation": q.get("explanation") or "Review the concept and retry a similar question.",
                "difficulty": "medium",
            } for q in official]

    # Any drill still empty becomes a lesson on the same skill, so the student
    # always receives teaching rather than an empty node.
    for node in unit["nodes"]:
        if node["node_type"] in ("practice_sprint", "quiz") and not node.get("questions"):
            app.logger.warning(
                "No questions available for %s node on %s; converting to a lesson.",
                node["node_type"], node["skill"]["skill_key"],
            )
            node["node_type"] = "lesson"
            node["xp_reward"] = learning.XP_BY_NODE["lesson"]
            teaching = learning._fallback_teaching(node)
            node["teaching"] = teaching
            node["steps"] = learning._interleave_lesson(teaching, [])

    saved = _persist_unit(user_id, unit, "Test Prep")
    if len(saved) != 5:
        raise ValueError("Path generation must produce exactly five usable steps.")
    return saved


def _get_test_prep_ai_chat_response(history, user_stats, stat_history="", user_id=None):
    if not os.getenv("GEMINI_API_KEY"):
        return "I'm in testing mode, but I'm saving our conversation!"

    # Gathered here rather than passed in: an earlier signature took these as
    # positional arguments and the call site shifted user_id into the quiz slot,
    # which silently blinded the coach to the student's own path.
    quiz_results = _get_quiz_results_for_prompt(user_id) if user_id else "No quiz data yet."
    sprint_results = _get_sprint_results_for_prompt(user_id) if user_id else "No sprint data yet."
    mastery_summary = learning.format_mastery_summary(_get_mastery_rows(user_id)) if user_id else "No graded work yet."

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
        "- **AI Path Generation**: The core of Mentics. Each test-prep path is a five-node unit shaped like a language-app unit: a Lesson that teaches a skill card by card with checks along the way, a Practice drill on that skill, a second Lesson, a cumulative Review, and finally a Boss Battle that sends the student to a full official practice test. Every node except the Boss Battle contains its own content inside Mentics.\n"
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
        f"## MEASURED SKILL MASTERY (from lessons, practice, and reviews inside Mentics)\n{mastery_summary}\n\n"
        f"## RECENT QUIZ PERFORMANCE (Incorrect Answers)\n{quiz_results}\n\n"

        f"## RECENT SPRINT PERFORMANCE (Incorrect Answers)\n{sprint_results}\n\n"
        f"This shows specific questions the user recently got wrong. Use this granular data to mentor them in their path."

        "## CORE COACHING DIRECTIVES (Your Rules of Engagement)\n"
        "0.  **Initial Greeting**: Your first reply must be a warm, concise welcome. Mention once that the student can ask naturally to regenerate, replace, or refocus their path and include the focus they want.\n"
        "1.  **Primary Goal: Path & App Support**: Your main purpose is to help the user with their current, active Path. Answer their questions about specific tasks, why they were assigned, and how to approach them. You must also be able to answer general questions about using the Mentics application's features as described above.\n"
        f"2.  **Path Regeneration Protocol**: If the student asks to regen, regenerate, replace, rebuild, redo, refocus, or create a path—even in casual language or as a follow-up to an earlier request—respond with exactly `{PATH_REGENERATION_CONTROL}` and nothing else. Mentics will use that private control response to perform the update. Never say you lack access to the backend, dashboard, path, or app. If the student is only exploring an idea and has not asked to change the path, coach them normally.\n"
        "3.  **Teach It Yourself**: Mentics paths carry their own lessons, practice, and reviews, so the student never needs to hunt for material. When they are stuck, TEACH the concept directly here with a concrete worked example, and point them at the specific step of their path that drills it. Only link outside Mentics for full-length official practice tests (College Board Bluebook, official ACT). Never answer with 'go read an article about this'.\n"
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


def _build_college_profile(user_id, college_context, chat_history):
    """Assemble what the college planner needs about one student."""
    stats = {}
    record = db.select_one("users", where={"id": user_id})
    if record:
        try:
            stats = json.loads(record["stats"]) or {}
        except (TypeError, ValueError):
            stats = {}

    grade = str(college_context.get("grade") or "").strip() or "not specified"
    stage = (college_context.get("planning_stage") or "researching").lower()

    academics = []
    if stats.get("gpa"):
        academics.append(f"GPA {stats['gpa']}")
    if stats.get("sat_ebrw") and stats.get("sat_math"):
        try:
            academics.append(
                f"SAT {int(stats['sat_ebrw']) + int(stats['sat_math'])} "
                f"(RW {stats['sat_ebrw']}, Math {stats['sat_math']})"
            )
        except (TypeError, ValueError):
            pass
    act_sections = [stats.get(k) for k in ("act_math", "act_reading", "act_science")]
    if all(act_sections):
        try:
            academics.append(f"ACT composite about {round(sum(int(v) for v in act_sections) / 3)}")
        except (TypeError, ValueError):
            pass

    progress = []
    if stats.get("colleges_researched"):
        progress.append(f"{stats['colleges_researched']} colleges researched")
    if stats.get("applications_submitted"):
        progress.append(f"{stats['applications_submitted']} applications submitted")
    if stats.get("essay_progress"):
        progress.append(
            "personal statement finalized" if str(stats["essay_progress"]) == "2"
            else "personal statement drafted"
        )
    for report in (college_context.get("reports") or [])[-6:]:
        text = str(report.get("report") or "").strip()
        if text:
            progress.append(f"Student report: {text[:700]}")
    done = db.execute(
        """SELECT skill_label FROM paths
           WHERE user_id=? AND category='College Planning' AND is_completed=True
             AND skill_label IS NOT NULL LIMIT 20""",
        (user_id,),
    ) or []
    taught = sorted({row["skill_label"] for row in done if row.get("skill_label")})

    latest_request = next(
        (m['content'] for m in reversed(chat_history or []) if m.get('role') == 'user'),
        "No specific request -- build the best next unit for their stage.",
    )

    return {
        "grade": grade,
        "stage": stage,
        "majors": college_context.get("majors") or "undecided",
        "target_colleges": college_context.get("target_colleges") or "none listed yet",
        "academics": ", ".join(academics) or "not provided",
        "progress": ", ".join(progress) or "nothing recorded yet",
        "taught_skills": ", ".join(taught) or "None yet",
        "latest_request": latest_request,
        "standing_focus": _describe_standing_focus(college_context),
        "chat_history": _format_chat_history_for_prompt(chat_history or []),
        "skill_options": learning.college_skill_options(stage),
    }


def _generate_and_save_new_college_path(user_id, college_context, chat_history=None):
    """Build the next college coaching loop: teach, act, then report back."""
    profile = _build_college_profile(user_id, college_context or {}, chat_history or [])
    unit = learning.build_college_unit(profile)

    saved = _persist_unit(user_id, unit, "College Planning")
    if len(saved) != len(learning.COLLEGE_SHAPE):
        raise ValueError("College path generation must produce a lesson and a real-world assignment.")
    return saved

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
@rate_limit('20/hour', name='tracker_analysis', message='Tracker analysis is limited while it studies your data. Try again shortly.')
def tracker_analysis(user):
    analysis_text = _get_tracker_ai_analysis(user)
    return jsonify({"analysis": analysis_text})
# --- Standard Routes ---


SSR_DIR = Path(app.root_path) / 'templates' / 'ssr'
_SSR_CACHE = {}


def _prerendered_markup(page):
    """Return build-time HTML for a public page, or None to render client-side.

    Prerendered markup is what crawlers and the first paint see; React hydrates
    it on load. Pages built per-session are deliberately absent here.
    """
    if page not in seo.PUBLIC_PAGES:
        return None
    if page in _SSR_CACHE:
        return _SSR_CACHE[page]
    candidate = SSR_DIR / f'{page}.html'
    try:
        # Guard against a page name escaping the SSR directory.
        candidate.resolve().relative_to(SSR_DIR.resolve())
        markup = candidate.read_text(encoding='utf-8')
    except (OSError, ValueError):
        markup = None
    if is_production:
        _SSR_CACHE[page] = markup
    return markup


def render_react(page, bootstrap=None, title=None, status=200):
    """Render the React application with server-verified bootstrap data."""
    data = dict(bootstrap or {})
    data['csrfToken'] = _csrf_token()
    g.csp_nonce = secrets.token_urlsafe(18)
    meta = seo.page_meta(page, title)
    return render_template(
        "react_app.html",
        page=page,
        bootstrap=data,
        title=meta['title'],
        meta=meta,
        structured_data=seo.structured_data() if page == 'landing' else None,
        site_verification=os.getenv('GOOGLE_SITE_VERIFICATION', ''),
        prerendered=_prerendered_markup(page),
        csp_nonce=g.csp_nonce,
        asset_version=os.getenv('VERCEL_GIT_COMMIT_SHA', 'dev')[:12],
    ), status


@app.route('/robots.txt')
def robots():
    return Response(seo.robots_txt(), mimetype='text/plain')


@app.route('/sitemap.xml')
def sitemap():
    return Response(seo.sitemap_xml(), mimetype='application/xml')


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
        allowed, retry_after = ratelimit.check(SIGNUP_LIMIT, name='signup')
        if not allowed:
            return ratelimit.too_many(
                retry_after, 'Too many accounts created from this location. Please try again later.')
        email = request.form.get("email", "").strip().lower()[:254]
        name = request.form.get("name", "").strip()[:100]
        raw_password = request.form.get("password", "")
        valid_email = re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email)
        if request.form.get("legal_acceptance") != "accepted":
            return render_react("signup", {
                "error": "You must agree to the Terms of Service and Privacy Policy to create an account."
            }, "Create Account | Mentics", 400)
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
                    "act_reading": "", "act_science": "", "gpa": "", "milestones": 0,
                    "legal_acceptance": {"terms_version": "2026-08-23", "privacy_version": "2026-08-23",
                                         "accepted_at": datetime.now().isoformat(timespec="seconds"), "method": "signup"}
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


# Verifying this throwaway hash costs the same as verifying a real one, so a
# failed sign-in takes the same time whether or not the address has an account.
# Without it, response timing reveals which emails are registered.
_DUMMY_PASSWORD_HASH = generate_password_hash(secrets.token_hex(16))

LOGIN_IP_LIMIT = os.getenv('RATE_LIMIT_LOGIN_IP', '10/minute')
LOGIN_IP_HOURLY_LIMIT = os.getenv('RATE_LIMIT_LOGIN_IP_HOURLY', '50/hour')
LOGIN_ACCOUNT_LIMIT = os.getenv('RATE_LIMIT_LOGIN_ACCOUNT', '8/hour')
SIGNUP_LIMIT = os.getenv('RATE_LIMIT_SIGNUP', '5/hour')


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("dashboard"))
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()[:254]
        password = request.form.get("password", "")

        # Throttle the source first, then the targeted account. The per-account
        # bucket is what stops credential stuffing that rotates through proxies.
        for rule, name in ((LOGIN_IP_LIMIT, 'login_ip'), (LOGIN_IP_HOURLY_LIMIT, 'login_ip_hourly')):
            allowed, retry_after = ratelimit.check(rule, name=name)
            if not allowed:
                return ratelimit.too_many(
                    retry_after, 'Too many sign-in attempts. Please wait before trying again.')
        if email:
            allowed, retry_after = ratelimit.check(
                LOGIN_ACCOUNT_LIMIT, name='login_account', key=f'e{email}')
            if not allowed:
                return ratelimit.too_many(
                    retry_after,
                    'This account has had too many failed sign-in attempts. Please wait before trying again.')

        user_record = db.select_one("users", where={"email": email}) if email else None
        stored_hash = user_record['password'] if user_record else _DUMMY_PASSWORD_HASH
        password_ok = len(password) <= 128 and check_password_hash(stored_hash, password)
        if user_record and password_ok:
            session.clear()
            session["user"] = user_record['email']
            session["user_id"] = user_record['id']
            session.permanent = True
            return redirect(url_for("dashboard"))
        error = "Invalid credentials"
    return render_react("login", {"error": error}, "Sign In | Mentics")

# NEW: Google Login Route


@app.route('/google-login')
@rate_limit('20/hour', name='google_login')
def google_login():
    # Preview URLs are unique per Vercel deployment and cannot be registered
    # permanently with Google. Start the flow on production so the OAuth state
    # cookie and callback always share the same stable hostname.
    if os.getenv("VERCEL_ENV") == "preview":
        app_url = os.getenv("PUBLIC_APP_URL", "https://mentics.vercel.app").rstrip('/')
        return redirect(f"{app_url}/google-login")

    # The app shows the notice immediately next to the Google control; retain
    # that acknowledgement through the third-party OAuth redirect.
    session['oauth_legal_notice'] = True
    redirect_uri = url_for('authorize', _external=True)
    return _get_oauth().google.authorize_redirect(redirect_uri)

# NEW: Google Authorize Route (Callback) - UPDATED


@app.route('/authorize')
@rate_limit('20/hour', name='oauth_callback')
def authorize():
    if not session.pop('oauth_legal_notice', False):
        return render_react(
            "login", {"error": "Start Google sign-in from Mentics so you can review the Terms and Privacy Policy."},
            "Sign In | Mentics", 400)
    google_oauth = _get_oauth().google
    try:
        # authorize_access_token() validates state, exchanges the code, and
        # verifies the ID token signature and nonce. A failure here means the
        # callback was forged, replayed, or expired.
        token = google_oauth.authorize_access_token()
    except Exception as error:
        app.logger.warning("Rejected Google OAuth callback: %s", error)
        return render_react(
            "login", {"error": "Google sign-in could not be completed. Please try again."},
            "Sign In | Mentics", 400)

    user_info = token.get('userinfo') or {}
    email = str(user_info.get('email') or '').strip().lower()[:254]
    # Google will happily issue a token for an unverified address. Accepting one
    # would let someone claim an account belonging to an email they do not own.
    if not email or not user_info.get('email_verified'):
        return render_react(
            "login", {"error": "Your Google account needs a verified email address to sign in."},
            "Sign In | Mentics", 400)
    display_name = str(user_info.get('name') or email.split('@')[0]).strip()[:100]

    user_record = db.select_one("users", where={"email": email})

    if user_record:
        authenticated_email = user_record['email']
        authenticated_id = user_record['id']
    else:

        password_hash = generate_password_hash(secrets.token_hex(32))
        user_id = db.insert("users", {
            "email": email,
            "name": display_name,
            "password": password_hash,
            "stats": json.dumps({
                "sat_ebrw": "", "sat_math": "", "act_math": "",
                "act_reading": "", "act_science": "", "gpa": "", "milestones": 0,
                "legal_acceptance": {"terms_version": "2026-08-23", "privacy_version": "2026-08-23",
                                     "accepted_at": datetime.now().isoformat(timespec="seconds"), "method": "google_oauth"}
            })
        })
        db.insert("gamification_stats", {
                  "user_id": user_id, "points": 0, "current_streak": 0})

        authenticated_email = email
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
@rate_limit('30/hour', name='set_timezone')
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
@rate_limit('40/hour', name='suggestion')
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
@rate_limit('20/hour', name='account_update', methods={'POST'})
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
@rate_limit('12/hour', name='test_path_build', methods={'POST'}, message='Path generation is limited to a few runs an hour. Try again shortly.')
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
@rate_limit('12/hour', name='college_path_build', methods={'POST'}, message='Path generation is limited to a few runs an hour. Try again shortly.')
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


def _path_snapshot(user_id, category):
    """Where the student currently stands in one path."""
    tasks = db.select(
        "paths",
        where={"user_id": user_id, "category": category, "is_active": True},
        order_by="task_order ASC",
    ) or []
    tasks = sorted(tasks, key=lambda t: t["task_order"])
    if not tasks:
        return None
    completed = sum(1 for t in tasks if t["is_completed"])
    current = next((t for t in tasks if not t["is_completed"]), None)
    return {
        "unitTitle": next((t.get("unit_title") for t in tasks if t.get("unit_title")), None),
        "completed": completed,
        "total": len(tasks),
        "currentStep": current["task_order"] if current else None,
        "currentTitle": (current or {}).get("description"),
        "currentSkill": (current or {}).get("skill_label"),
        "currentType": (current or {}).get("node_type"),
        "steps": [{
            "order": t["task_order"],
            "nodeType": t.get("node_type"),
            "skill": t.get("skill_label"),
            "done": bool(t["is_completed"]),
        } for t in tasks],
    }


def _practice_totals(user_id):
    """Every graded answer the student has given inside Mentics."""
    rows = db.execute_for_one(
        """SELECT
             (SELECT COUNT(*) FROM quiz_results WHERE user_id=?) AS quiz_total,
             (SELECT COUNT(*) FROM quiz_results WHERE user_id=? AND is_correct=1) AS quiz_correct,
             (SELECT COUNT(*) FROM sprint_results WHERE user_id=?) AS sprint_total,
             (SELECT COUNT(*) FROM sprint_results WHERE user_id=? AND is_correct=1) AS sprint_correct,
             (SELECT COUNT(*) FROM lesson_answers WHERE user_id=?) AS lesson_total,
             (SELECT COUNT(*) FROM lesson_answers WHERE user_id=? AND is_correct=1) AS lesson_correct""",
        (user_id,) * 6,
    ) or {}
    total = sum(rows.get(k) or 0 for k in ("quiz_total", "sprint_total", "lesson_total"))
    correct = sum(rows.get(k) or 0 for k in ("quiz_correct", "sprint_correct", "lesson_correct"))
    return {
        "answered": total,
        "correct": correct,
        "accuracy": round(correct / total * 100) if total else None,
    }


@app.route("/dashboard/stats", methods=["GET"])
@login_required
def stats(user):
    """A snapshot built from what the student has actually done, not just typed in.

    The old page showed four numbers the student entered by hand, which is why it
    never reflected the work. Everything here except GPA now comes from graded
    answers, logged tests, and live path state.
    """
    stats = user.get_stats()
    user_id = user.data['id']

    def as_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    test_path = stats.get("test_path") or {}
    # Scores may be entered on the profile or while building a test path.
    # The profile should show one coherent snapshot, not make students re-enter them.
    sat_ebrw = as_int(stats.get("sat_ebrw") or test_path.get("current_sat_ebrw"))
    sat_math = as_int(stats.get("sat_math") or test_path.get("current_sat_math"))
    sat_total = sat_ebrw + sat_math if sat_ebrw and sat_math else as_int(stats.get("sat_total"))
    act_math = as_int(stats.get("act_math") or test_path.get("current_act_math"))
    act_reading = as_int(stats.get("act_reading") or test_path.get("current_act_reading"))
    act_science = as_int(stats.get("act_science") or test_path.get("current_act_science"))
    act_sections = [act_math, act_reading, act_science]
    act_composite = as_int(stats.get("act_composite") or test_path.get("current_act_composite"))
    act_average = act_composite or (round(sum(v for v in act_sections if v) / len([v for v in act_sections if v]))
                                    if any(act_sections) else None)
    goal_sat = as_int(test_path.get("desired_sat"))
    goal_act = as_int(test_path.get("desired_act"))

    # Mastery, ranked. This is the part that makes the page reflect the paths.
    mastery = sorted(_get_mastery_rows(user_id), key=lambda r: (r["accuracy"], -r["attempts"]))
    measured = [m for m in mastery if m["attempts"] >= 3]
    by_subject = {}
    for row in mastery:
        bucket = by_subject.setdefault(row["subject"] or "Other", {"attempts": 0, "correct": 0})
        bucket["attempts"] += row["attempts"]
        bucket["correct"] += row["correct"]
    subjects = [{
        "subject": name,
        "accuracy": round(v["correct"] / v["attempts"] * 100) if v["attempts"] else 0,
        "attempts": v["attempts"],
    } for name, v in by_subject.items() if v["attempts"]]
    subjects.sort(key=lambda s: -s["attempts"])

    game = db.select_one("gamification_stats", where={"user_id": user_id}) or {}
    all_tasks = db.select("paths", where={"user_id": user_id}) or []

    open_mistakes = db.execute_for_one(
        "SELECT COUNT(*) AS n FROM mistake_bank WHERE user_id=? AND resolved=False", (user_id,)
    ) or {}

    return render_react("stats", {
        "name": user.get_name(),
        "gpa": stats.get("gpa", ""),
        "satEbrw": sat_ebrw, "satMath": sat_math, "satTotal": sat_total,
        "actMath": act_math, "actReading": act_reading,
        "actScience": act_science, "actAverage": act_average, "actComposite": act_composite,
        "goalSat": goal_sat, "goalAct": goal_act,
        "testDate": test_path.get("test_date"),
        "points": game.get("points") or 0,
        "streak": game.get("current_streak") or 0,
        "practice": _practice_totals(user_id),
        "subjects": subjects,
        "weakest": [{
            "skill": m["skill_label"], "subject": m["subject"],
            "accuracy": round(m["accuracy"] * 100), "attempts": m["attempts"], "level": m["level"],
        } for m in measured[:5]],
        "strongest": [{
            "skill": m["skill_label"], "subject": m["subject"],
            "accuracy": round(m["accuracy"] * 100), "attempts": m["attempts"], "level": m["level"],
        } for m in reversed(measured[-5:])] if measured else [],
        "openMistakes": open_mistakes.get("n") or 0,
        "testPath": _path_snapshot(user_id, "Test Prep"),
        "collegePath": _path_snapshot(user_id, "College Planning"),
        "collegesResearched": as_int(stats.get("colleges_researched")) or 0,
        "applicationsSubmitted": as_int(stats.get("applications_submitted")) or 0,
        "essayProgress": as_int(stats.get("essay_progress")),
        "totalTestPrepCompleted": sum(
            1 for t in all_tasks if t['is_completed'] and t['category'] == 'Test Prep'),
        "totalCollegePlanningCompleted": sum(
            1 for t in all_tasks if t['is_completed'] and t['category'] == 'College Planning'),
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
@rate_limit('60/hour', name='quiz_results')
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

        _repair_legacy_active_path(user_id, category)
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
                    "error": "I couldn't generate your next coaching step. Your current path is unchanged; please try again."
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
                    "task_content_id": r.get('task_content_id'),
                    # Paths generated before the lesson engine kept their guide in
                    # a separate article, which the step still links to.
                    "secondary_content_id": r.get('secondary_content_id'),
                    "node_type": r.get('node_type'),
                    "skill_label": r.get('skill_label'),
                    "subject": r.get('subject'),
                    "objective": r.get('objective'),
                    "xp_reward": r.get('xp_reward') or 10,
                    "unit_title": r.get('unit_title'),
                })
            return jsonify(tasks_with_subtasks)

        return jsonify([])
    except Exception as e:
        print(f"API tasks error for category {category}: {e}")
        return jsonify({"error": "An error occurred"}), 500


@app.route('/api/quiz/<int:task_id>')
@login_required
@rate_limit('60/hour', name='quiz')
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
            "options": json.loads(q['options']),
            "correct_option": q.get('correct_option', 0),
            "explanation": q.get('explanation', '')
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
    if status == 'complete' and task_info.get('task_format') in {'lesson', 'quiz', 'practice_sprint'}:
        return jsonify({
            "success": False,
            "error": "Finish the activity before completing this path step."
        }), 409
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

    claimed = _record_task_completion(user_id, task_info)
    if claimed:
        description = task_info['description']
        task_type = task_info['type']

        # --- GAMIFICATION LOGIC ---
        # Lesson and drill nodes carry their own XP value; older rows and
        # personal steps fall back to the original flat award.
        points_target = task_info.get('xp_reward') or (25 if task_type == 'milestone' else 10)
        if "boss battle" in description.lower():
            points_target = max(points_target, 100)
        already_awarded = task_info.get('xp_awarded') or 0
        points_to_add = max(0, points_target - already_awarded)
        if points_target > already_awarded:
            db.execute_write(
                "UPDATE paths SET xp_awarded=? WHERE id=? AND user_id=?",
                (points_target, task_id, user_id),
            )
        _award_xp(user_id, points_to_add)
    else:
        return jsonify({"success": True, "already_completed": True})

    return jsonify({"success": True})


@app.route('/api/college_task_report', methods=['POST'])
@login_required
@rate_limit('12/hour', name='college_task_report')
def college_task_report(user):
    """Close one real-world assignment and immediately build the next coaching loop."""
    user_id = user.data['id']
    data = request.get_json(silent=True) or {}
    task_id = data.get('taskId')
    report = str(data.get('report') or '').strip()
    if not task_id or not 20 <= len(report) <= 4000:
        return jsonify({"error": "Please share a short, specific report before continuing."}), 400

    task = db.select_one('paths', where={
        'id': task_id, 'user_id': user_id, 'category': 'College Planning',
        'is_active': True, 'task_format': 'milestone',
    })
    if not task:
        return jsonify({"error": "That college assignment is no longer active."}), 404
    blocked = db.execute_for_one(
        """SELECT id FROM paths WHERE user_id=? AND category='College Planning'
           AND is_active=True AND task_order<? AND is_completed=False LIMIT 1""",
        (user_id, task['task_order']),
    )
    if blocked:
        return jsonify({"error": "Finish the lesson before reporting back."}), 409

    if not task.get('is_completed') and _record_task_completion(user_id, task):
        points_target = task.get('xp_reward') or 90
        already_awarded = task.get('xp_awarded') or 0
        points_to_add = max(0, points_target - already_awarded)
        if points_to_add:
            db.execute_write('UPDATE paths SET xp_awarded=? WHERE id=? AND user_id=?',
                             (points_target, task_id, user_id))
            _award_xp(user_id, points_to_add)

    stats = user.get_stats()
    college_path = dict(stats.get('college_path') or {})
    reports = list(college_path.get('reports') or [])[-11:]
    reports.append({
        'task': task['description'], 'report': report,
        'reported_at': datetime.now().isoformat(timespec='seconds'),
    })
    college_path['reports'] = reports
    stats['college_path'] = college_path
    user.set_stats(stats)
    log_activity(user_id, 'college_task_reported', {'description': task['description']})

    history_row = db.select_one('chat_conversations', where={
        'user_id': user_id, 'category': 'College Planning'})
    history = json.loads(history_row['history']) if history_row and history_row.get('history') else []
    try:
        tasks = _generate_and_save_new_college_path(user_id, college_path, history)
    except Exception:
        app.logger.exception('College next-step generation failed for user %s', user_id)
        return jsonify({"error": "Your report was saved, but the next step could not be built yet. Please try again."}), 502
    return jsonify({"success": True, "tasks": tasks})


def _remember_path_focus(user, category, history):
    """Persist the focus a student asked for so it outlives one regeneration.

    Without this the request only shapes the unit generated in that moment; the
    next unit forgets it and drifts back to whatever the scores suggest, which
    reads as the app ignoring what they said.
    """
    request_text = next(
        (m['content'] for m in reversed(history or []) if m.get('role') == 'user'), ""
    ).strip()
    if not request_text:
        return
    stats = user.get_stats()
    key = "college_path" if category == 'College Planning' else "test_path"
    section = dict(stats.get(key) or {})
    section["focus_request"] = request_text[:600]
    section["focus_set_at"] = date.today().isoformat()
    stats[key] = section
    user.set_stats(stats)


def _describe_standing_focus(section):
    """Render a previously stated focus for the planner, with its age."""
    focus = (section or {}).get("focus_request")
    if not focus:
        return "None stated."
    when = (section or {}).get("focus_set_at")
    if when:
        try:
            days = (date.today() - date.fromisoformat(when)).days
            age = "today" if days == 0 else f"{days} day(s) ago"
            return f'"{focus}" (asked {age})'
        except (TypeError, ValueError):
            pass
    return f'"{focus}"'


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
        expected = len(learning.COLLEGE_SHAPE) if category == 'College Planning' else 5
        if len(new_tasks) != expected:
            raise ValueError("Regeneration did not save the expected path steps.")
    except Exception:
        app.logger.exception(
            "Chat path regeneration failed for user %s (%s)", user_id, category
        )
        return jsonify({
            "error": "I couldn't generate your next coaching step. Your current path is unchanged; please try again."
        }), 502

    reply = ("Your next college coaching loop is ready. I shaped it around your latest request and our conversation."
             if category == 'College Planning' else
             "Your new five-step path is ready. I shaped it around your latest request and our conversation.")
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


IMPORT_TOKEN = os.getenv("IMPORT_API_TOKEN")
MAX_IMPORT_BATCH = 500


@app.route("/api/import_official_questions", methods=['POST'])
@rate_limit('10/hour', name='question_import')
def import_official_questions():
    """Bulk import official SAT/ACT questions. Format: JSON array of question objects.

    This writes directly into the shared question bank, so it is an operator
    tool, not a user-facing endpoint. It stays closed unless IMPORT_API_TOKEN is
    configured, and the token is compared in constant time.
    """
    if not IMPORT_TOKEN:
        return jsonify({"error": "Question import is not enabled."}), 404
    supplied = request.headers.get("X-Import-Token", "")
    if not hmac.compare_digest(supplied, IMPORT_TOKEN):
        return jsonify({"error": "Not authorized."}), 401
    try:
        data = request.get_json(silent=True) or {}
        questions = data.get("questions", [])

        if not isinstance(questions, list):
            return jsonify({"error": "Questions must be an array"}), 400
        if len(questions) > MAX_IMPORT_BATCH:
            return jsonify({
                "error": f"Send at most {MAX_IMPORT_BATCH} questions per request."
            }), 413
        
        imported_count = 0
        errors = []
        
        for idx, q in enumerate(questions):
            try:
                # Validate required fields
                if not all(k in q for k in ['test_type', 'subject', 'topic', 'question_text', 'options', 'correct_option']):
                    errors.append(f"Question {idx}: Missing required field")
                    continue
                
                # Ensure options is a list
                options = q['options'] if isinstance(q['options'], list) else json.loads(q['options'])
                
                db.insert("official_questions", {
                    "test_type": q.get('test_type', 'SAT'),  # SAT or ACT
                    "subject": q.get('subject', 'Math'),  # Math, Reading/Writing
                    "topic": q.get('topic', 'General'),
                    "difficulty": q.get('difficulty', 'medium'),
                    "question_text": q['question_text'],
                    "options": json.dumps(options),
                    "correct_option": int(q['correct_option']),
                    "explanation": q.get('explanation', ''),
                    "source_url": q.get('source_url', ''),
                    "source_or_prompt": q.get('source_or_prompt', ''),
                })
                imported_count += 1
            except Exception as error:
                app.logger.warning("Question import rejected row %s: %s", idx, error)
                errors.append(f"Question {idx}: could not be imported")

        return jsonify({
            "success": imported_count > 0,
            "imported": imported_count,
            "total": len(questions),
            "errors": errors if errors else None
        }), 200 if imported_count > 0 else 400

    except Exception as error:
        app.logger.exception("Question import failed: %s", error)
        return jsonify({"error": "Import failed."}), 500


@app.route("/api/chat", methods=['POST'])
@login_required
@rate_limit('8/minute', name='chat_burst')
@rate_limit('60/hour', name='chat', message='You have reached the coaching limit for this hour. Your conversation is saved.')
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
        _remember_path_focus(user, category, history)
        return _regenerate_path_from_chat(user_id, user.get_stats(), category, history)

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
        _remember_path_focus(user, category, history)
        return _regenerate_path_from_chat(user_id, user.get_stats(), category, history)

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
@rate_limit('20/hour', name='reset_chat')
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
@rate_limit('60/hour', name='update_stats')
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
@rate_limit('60/hour', name='add_task')
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
@rate_limit('100/hour', name='add_subtask')
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
@rate_limit('12/hour', name='essay', message='Essay reviews are limited to twelve an hour so feedback stays thorough.')
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
    if _get_gemini_client() is None:
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
        "viewerId": user.data['id'],
        "posts": posts_with_replies,
        "todaysThreads": todays_threads,
        "searchQuery": search_query,
    }, "Community | Mentics")


@app.route('/api/posts', methods=['POST'])
@login_required
@rate_limit('10/hour', name='forum_post', message='You have posted several discussions recently. Give others a moment to reply.')
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
@rate_limit('30/hour', name='forum_reply')
def create_reply(user):
    data = request.get_json(silent=True) or {}
    try:
        post_id = int(data.get('post_id'))
    except (TypeError, ValueError):
        post_id = None
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


@app.route('/api/posts/<int:post_id>', methods=['PATCH'])
@login_required
@rate_limit('30/hour', name='forum_edit')
def update_post(user, post_id):
    post = db.select_one('forum_posts', where={'id': post_id})
    if not post:
        return jsonify({'success': False, 'error': 'Discussion not found'}), 404
    if post['user_id'] != user.data['id']:
        return jsonify({'success': False, 'error': 'You can only edit your own discussions'}), 403
    data = request.get_json(silent=True) or {}
    title = str(data.get('title') or '').strip()[:200]
    content = str(data.get('content') or '').strip()[:5000]
    if not title or not content:
        return jsonify({'success': False, 'error': 'Title and content are required'}), 400
    db.update('forum_posts', {'title': title, 'content': content}, where={'id': post_id})
    return jsonify({'success': True})


@app.route('/api/replies/<int:reply_id>', methods=['PATCH'])
@login_required
@rate_limit('30/hour', name='forum_edit')
def update_reply(user, reply_id):
    reply = db.select_one('forum_replies', where={'id': reply_id})
    if not reply:
        return jsonify({'success': False, 'error': 'Reply not found'}), 404
    if reply['user_id'] != user.data['id']:
        return jsonify({'success': False, 'error': 'You can only edit your own replies'}), 403
    content = str((request.get_json(silent=True) or {}).get('content') or '').strip()[:5000]
    if not content:
        return jsonify({'success': False, 'error': 'Reply content is required'}), 400
    db.update('forum_replies', {'content': content}, where={'id': reply_id})
    return jsonify({'success': True})


# --- SAT Battle Arena ------------------------------------------------------
# These original, compact questions keep a battle fast and fair. The server
# owns the answer key and timestamps; clients receive only the prompt/options.
SAT_BATTLE_QUESTION_POOL = [
    {"question_text": "If 3x + 8 = 29, what is x?", "options": ["5", "7", "9", "11"], "correct_option": 1, "skill": "Algebra"},
    {"question_text": "What is the value of 2a² - 3 when a = 4?", "options": ["13", "29", "32", "61"], "correct_option": 1, "skill": "Algebra"},
    {"question_text": "A line has slope 3 and passes through (2, 5). What is its y-intercept?", "options": ["-1", "1", "3", "11"], "correct_option": 0, "skill": "Linear equations"},
    {"question_text": "A rectangle has length 12 and width 5. What is its area?", "options": ["17", "34", "60", "120"], "correct_option": 2, "skill": "Geometry"},
    {"question_text": "Which expression is equivalent to (x + 4)(x - 4)?", "options": ["x² - 16", "x² + 16", "x² - 8x + 16", "x² + 8x - 16"], "correct_option": 0, "skill": "Algebra"},
    {"question_text": "The mean of 6, 8, 10, and n is 9. What is n?", "options": ["9", "10", "11", "12"], "correct_option": 3, "skill": "Data analysis"},
    {"question_text": "If 40% of a number is 28, what is the number?", "options": ["56", "70", "84", "112"], "correct_option": 1, "skill": "Percentages"},
    {"question_text": "Which transition most logically signals a contrast?", "options": ["For example,", "Therefore,", "However,", "Similarly,"], "correct_option": 2, "skill": "Transitions"},
    {"question_text": "Which sentence uses a semicolon correctly?", "options": ["The test was hard; because I rushed.", "I reviewed my errors; then I tried again.", "I reviewed my errors; and then tried again.", "Because I reviewed; my errors improved."], "correct_option": 1, "skill": "Conventions"},
    {"question_text": "A study found that students who slept more reported better focus. Which conclusion is best supported?", "options": ["Sleep always causes better grades.", "The study proves sleep is the only factor in focus.", "More sleep was associated with better reported focus in this study.", "Students should never study at night."], "correct_option": 2, "skill": "Reading and analysis"},
]
SAT_BATTLE_QUESTION_COUNT = 5
SAT_BATTLE_DURATION_SECONDS = 120


def _utc_now():
    return datetime.now(ZoneInfo("UTC"))


def _battle_time(value):
    if not value:
        return None
    parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=ZoneInfo("UTC"))


def _battle_questions():
    return secrets.SystemRandom().sample(SAT_BATTLE_QUESTION_POOL, SAT_BATTLE_QUESTION_COUNT)


def _battle_answers(value):
    try:
        answers = json.loads(value or '[]')
    except (TypeError, ValueError):
        answers = []
    return answers if isinstance(answers, list) else []


def _battle_score(questions, answers):
    selected = {item.get('question_index'): item.get('selected_option') for item in answers if isinstance(item, dict)}
    return sum(1 for index, question in enumerate(questions) if selected.get(index) == question['correct_option'])


def _battle_rating(user_id, user_name, outcome):
    stats = db.select_one('sat_battle_stats', where={'user_id': user_id})
    if not stats:
        stats = {'user_id': user_id, 'user_name': user_name, 'rating': 1000, 'wins': 0, 'losses': 0, 'draws': 0, 'battles_played': 0}
        db.insert('sat_battle_stats', stats)
    delta = {'win': 24, 'loss': -14, 'draw': 4}[outcome]
    db.update('sat_battle_stats', {
        'user_name': user_name,
        'rating': max(800, int(stats['rating']) + delta),
        'wins': int(stats['wins']) + (outcome == 'win'),
        'losses': int(stats['losses']) + (outcome == 'loss'),
        'draws': int(stats['draws']) + (outcome == 'draw'),
        'battles_played': int(stats['battles_played']) + 1,
    }, where={'user_id': user_id})


def _finish_battle_if_ready(battle):
    if not battle or battle['status'] != 'active':
        return battle
    now = _utc_now()
    started = _battle_time(battle.get('started_at')) or now
    timed_out = (now - started).total_seconds() >= SAT_BATTLE_DURATION_SECONDS
    challenger_done = bool(battle.get('challenger_answers'))
    opponent_done = bool(battle.get('opponent_answers'))
    if not (timed_out or (challenger_done and opponent_done)):
        return battle
    questions = json.loads(battle['questions'])
    challenger_score = _battle_score(questions, _battle_answers(battle.get('challenger_answers')))
    opponent_score = _battle_score(questions, _battle_answers(battle.get('opponent_answers')))
    challenger_time = _battle_time(battle.get('challenger_finished_at')) or now
    opponent_time = _battle_time(battle.get('opponent_finished_at')) or now
    winner_id = None
    if challenger_score > opponent_score or (challenger_score == opponent_score and challenger_score and challenger_time < opponent_time):
        winner_id = battle['challenger_id']
    elif opponent_score > challenger_score or (challenger_score == opponent_score and opponent_score and opponent_time < challenger_time):
        winner_id = battle['opponent_id']
    completed_at = now.isoformat()
    updated = db.execute_write(
        "UPDATE sat_battles SET status='complete', winner_id=?, completed_at=? WHERE id=? AND status='active'",
        (winner_id, completed_at, battle['id']))
    if updated:
        challenger_outcome = 'draw' if winner_id is None else 'win' if winner_id == battle['challenger_id'] else 'loss'
        opponent_outcome = 'draw' if winner_id is None else 'win' if winner_id == battle['opponent_id'] else 'loss'
        _battle_rating(battle['challenger_id'], battle['challenger_name'], challenger_outcome)
        _battle_rating(battle['opponent_id'], battle['opponent_name'], opponent_outcome)
    return db.select_one('sat_battles', where={'id': battle['id']})


def _battle_payload(battle, user_id):
    if battle and battle['status'] == 'waiting':
        created_at = _battle_time(battle.get('created_at'))
        if created_at and (_utc_now() - created_at).total_seconds() > 600:
            db.execute_write("UPDATE sat_battles SET status='expired' WHERE id=? AND status='waiting'", (battle['id'],))
            battle = db.select_one('sat_battles', where={'id': battle['id']})
    battle = _finish_battle_if_ready(battle)
    if not battle or user_id not in (battle['challenger_id'], battle.get('opponent_id')):
        return None
    is_challenger = battle['challenger_id'] == user_id
    opponent_name = battle.get('opponent_name') if is_challenger else battle['challenger_name']
    own_answers = _battle_answers(battle.get('challenger_answers') if is_challenger else battle.get('opponent_answers'))
    result = {
        'id': battle['id'], 'status': battle['status'], 'opponentName': opponent_name,
        'startedAt': battle.get('started_at'), 'durationSeconds': SAT_BATTLE_DURATION_SECONDS,
        'submitted': bool(own_answers), 'createdAt': battle.get('created_at'),
    }
    if battle['status'] in {'active', 'complete'}:
        questions = json.loads(battle['questions'])
        result['questions'] = [{'question_text': q['question_text'], 'options': q['options'], 'skill': q['skill']} for q in questions]
    if battle['status'] == 'complete':
        questions = json.loads(battle['questions'])
        challenger_score = _battle_score(questions, _battle_answers(battle.get('challenger_answers')))
        opponent_score = _battle_score(questions, _battle_answers(battle.get('opponent_answers')))
        own_score, opponent_score = (challenger_score, opponent_score) if is_challenger else (opponent_score, challenger_score)
        result.update({'winnerId': battle.get('winner_id'), 'youWon': battle.get('winner_id') == user_id, 'draw': battle.get('winner_id') is None, 'yourScore': own_score, 'opponentScore': opponent_score, 'answerKey': [q['correct_option'] for q in questions]})
    return result


def _user_current_battle(user_id):
    return db.execute_for_one(
        "SELECT * FROM sat_battles WHERE (challenger_id=? OR opponent_id=?) AND status IN ('waiting', 'active') ORDER BY created_at DESC LIMIT 1",
        (user_id, user_id))


@app.route('/battles')
@login_required
def battle_arena(user):
    current = _user_current_battle(user.data['id'])
    leaderboard = db.execute("SELECT user_id, user_name, rating, wins, losses, battles_played FROM sat_battle_stats ORDER BY rating DESC, wins DESC LIMIT 10")
    spotlight = db.execute("SELECT * FROM sat_battles WHERE status='complete' ORDER BY completed_at DESC LIMIT 1")
    return render_react('battles', {
        'name': user.get_name(),
        'currentBattle': _battle_payload(current, user.data['id']) if current else None,
        'leaderboard': leaderboard,
        'spotlight': spotlight[0] if spotlight else None,
    }, 'SAT Battles | Mentics')


@app.route('/api/sat-battles/queue', methods=['POST'])
@login_required
@rate_limit('12/hour', name='sat_battle_queue', message='Take a moment before searching for another battle.')
def queue_sat_battle(user):
    current = _user_current_battle(user.data['id'])
    if current:
        return jsonify(_battle_payload(current, user.data['id']))
    now = _utc_now()
    for waiting_battle in db.execute("SELECT id, created_at FROM sat_battles WHERE status='waiting'"):
        created_at = _battle_time(waiting_battle.get('created_at'))
        if created_at and (now - created_at).total_seconds() > 600:
            db.update('sat_battles', {'status': 'expired'}, where={'id': waiting_battle['id']})
    paired = db.execute_returning_one(
        """UPDATE sat_battles SET opponent_id=?, opponent_name=?, status='active', started_at=?
           WHERE id=(SELECT id FROM sat_battles WHERE status='waiting' AND challenger_id != ? ORDER BY created_at ASC LIMIT 1)
             AND status='waiting' RETURNING *""",
        (user.data['id'], user.get_name(), _utc_now().isoformat(), user.data['id']))
    if paired:
        return jsonify(_battle_payload(paired, user.data['id']))
    battle_id = db.insert('sat_battles', {
        'status': 'waiting', 'challenger_id': user.data['id'], 'challenger_name': user.get_name(),
        'questions': json.dumps(_battle_questions()),
    })
    return jsonify(_battle_payload(db.select_one('sat_battles', where={'id': battle_id}), user.data['id']))


@app.route('/api/sat-battles/<int:battle_id>')
@login_required
def get_sat_battle(user, battle_id):
    battle = db.select_one('sat_battles', where={'id': battle_id})
    payload = _battle_payload(battle, user.data['id'])
    if not payload:
        return jsonify({'error': 'Battle not found'}), 404
    return jsonify(payload)


@app.route('/api/sat-battles/<int:battle_id>/cancel', methods=['POST'])
@login_required
def cancel_sat_battle(user, battle_id):
    cancelled = db.execute_write(
        "UPDATE sat_battles SET status='expired' WHERE id=? AND challenger_id=? AND status='waiting'",
        (battle_id, user.data['id']))
    if not cancelled:
        return jsonify({'error': 'This match can no longer be cancelled'}), 409
    return jsonify({'success': True})


@app.route('/api/sat-battles/<int:battle_id>/submit', methods=['POST'])
@login_required
@rate_limit('20/hour', name='sat_battle_submit')
def submit_sat_battle(user, battle_id):
    battle = db.select_one('sat_battles', where={'id': battle_id})
    if not battle or user.data['id'] not in (battle['challenger_id'], battle.get('opponent_id')):
        return jsonify({'error': 'Battle not found'}), 404
    battle = _finish_battle_if_ready(battle)
    if battle['status'] != 'active':
        return jsonify({'error': 'This battle has already ended'}), 409
    is_challenger = user.data['id'] == battle['challenger_id']
    answer_column = 'challenger_answers' if is_challenger else 'opponent_answers'
    finished_column = 'challenger_finished_at' if is_challenger else 'opponent_finished_at'
    if battle.get(answer_column):
        return jsonify({'error': 'Your answers are already locked'}), 409
    answers = (request.get_json(silent=True) or {}).get('answers')
    if not isinstance(answers, list) or len(answers) != SAT_BATTLE_QUESTION_COUNT:
        return jsonify({'error': 'Answer every question before locking your battle.'}), 400
    cleaned, seen = [], set()
    for answer in answers:
        try:
            question_index = int(answer.get('question_index'))
            selected_option = int(answer.get('selected_option'))
        except (AttributeError, TypeError, ValueError):
            return jsonify({'error': 'One of your answers is invalid.'}), 400
        if question_index in seen or not 0 <= question_index < SAT_BATTLE_QUESTION_COUNT or not 0 <= selected_option < 4:
            return jsonify({'error': 'One of your answers is invalid.'}), 400
        seen.add(question_index); cleaned.append({'question_index': question_index, 'selected_option': selected_option})
    db.update('sat_battles', {answer_column: json.dumps(cleaned), finished_column: _utc_now().isoformat()}, where={'id': battle_id})
    return jsonify(_battle_payload(db.select_one('sat_battles', where={'id': battle_id}), user.data['id']))


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
# Counters share the application database so limits hold across serverless
# invocations. Set RATE_LIMITS_ENABLED=0 only for local load testing.
ratelimit.init_app(app, db, enabled=os.getenv('RATE_LIMITS_ENABLED', '1') != '0')

if not is_production or os.getenv('INIT_DB_ON_STARTUP') == '1':
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
