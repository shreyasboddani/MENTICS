from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dbhelper import DatabaseHandler
from userhelper import User
from functools import wraps
import json
import openai
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for session management
app.url_map.strict_slashes = False

db = DatabaseHandler("users.db")

# Setup OpenAI API Key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Create database and user table if it doesn't exist


def init_db():
    db.create_table("users", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "email": "TEXT NOT NULL UNIQUE",
        "password": "TEXT NOT NULL",
        "stats": "TEXT NOT NULL"
    })


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# Home page


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
    test_path = stats.get("test_path", {})
    error = None

    if request.method == "POST":
        # Get form data
        test_path = {
            "desired_sat": request.form.get("desired_sat", ""),
            "desired_act": request.form.get("desired_act", ""),
            "strengths": request.form.get("strengths", ""),
            "weaknesses": request.form.get("weaknesses", ""),
            "test_date": request.form.get("test_date", ""),
            "test_time": request.form.get("test_time", "")
        }
        stats["test_path"] = test_path
        user.set_stats(stats)
        return redirect(url_for("test_path_view"))

    # Pre-fill form if data exists
    return render_template(
        "test_path_builder.html",
        desired_sat=test_path.get("desired_sat", ""),
        desired_act=test_path.get("desired_act", ""),
        strengths=test_path.get("strengths", ""),
        weaknesses=test_path.get("weaknesses", ""),
        test_date=test_path.get("test_date", ""),
        test_time=test_path.get("test_time", ""),
        error=error
    )


@app.route("/dashboard/test-path-view")
@login_required
def test_path_view():
    user = User.from_session(db, session)
    if not user:
        return redirect(url_for("login"))
    stats = user.get_stats()
    test_path = stats.get("test_path", {})
    return render_template(
        "test_path_view.html",
        test_path=test_path
    )


def _generate_mock_tasks(strengths, weaknesses, num_tasks=5):
    """
    Generates a list of mock tasks. Used as a fallback if the AI API fails.
    """
    tasks = []
    # A very basic "AI" logic for demonstration
    if "geometry" in weaknesses.lower():
        tasks.append(
            {"description": "Focus on circle theorems and properties of triangles.", "status": "pending"})
    if "punctuation" in weaknesses.lower():
        tasks.append(
            {"description": "Complete a drill on comma, semicolon, and colon usage.", "status": "pending"})
    if "algebra" in strengths.lower():
        tasks.append(
            {"description": "Solidify your algebra skills with advanced function problems.", "status": "pending"})

    # Generic tasks to fill up the list
    generic_tasks = [
        {"description": "Complete a timed mini-section for your weakest subject.", "status": "pending"},
        {"description": "Review 20 new vocabulary words using flashcards.", "status": "pending"},
        {"description": "Analyze the structure of a sample essay prompt.", "status": "pending"},
        {"description": "Review 20 new vocabulary words using flashcards.", "status": "pending"},
        {"description": "Analyze the structure of a sample essay prompt.", "status": "pending"}
    ]

    while len(tasks) < num_tasks and generic_tasks:
        tasks.append(generic_tasks.pop(0))

    # Ensure the last task is a milestone
    if tasks:
        tasks[-1]['is_milestone'] = True

    return tasks[:num_tasks]


def _generate_ai_tasks(strengths, weaknesses, num_tasks=5):
    """
    Calls the OpenAI API to generate personalized tasks based on user input.
    """
    if not openai.api_key:
        print("Warning: OPENAI_API_KEY environment variable not set. Falling back to mock tasks.")
        return _generate_mock_tasks(strengths, weaknesses, num_tasks)

    prompt_content = (
        f"Based on a student's strengths in '{strengths}' and weaknesses in '{weaknesses}', "
        f"create a list of exactly {num_tasks} personalized tasks for SAT/ACT test prep. "
        "The last task must be a milestone task, like taking a practice test. "
        "Return the response as a single, valid JSON object with a key 'tasks' which is an array of objects. "
        "Each object must have two keys: 'description' (a string) and 'is_milestone' (a boolean)."
    )

    try:
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo-1106",  # A model that supports JSON mode
            messages=[
                {"role": "system", "content": "You are an expert test prep tutor that creates personalized study plans and responds in valid JSON."},
                {"role": "user", "content": prompt_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        response_text = completion.choices[0].message.content
        data = json.loads(response_text)
        tasks = data.get("tasks", [])

        # Validate and clean the response
        if not isinstance(tasks, list):
            raise ValueError("AI response did not contain a 'tasks' list.")

        processed_tasks = []
        for task in tasks:
            if 'description' in task and isinstance(task['description'], str):
                processed_tasks.append({
                    "description": task['description'],
                    "status": "pending",
                    "is_milestone": task.get('is_milestone', False)
                })

        if not processed_tasks:
            raise ValueError("AI response contained no valid tasks.")

        processed_tasks[-1]['is_milestone'] = True
        return processed_tasks[:num_tasks]

    except Exception as e:
        print(f"Error calling OpenAI or parsing response: {e}")
        return _generate_mock_tasks(strengths, weaknesses, num_tasks)


@app.route("/api/generate-tasks")
@login_required
def generate_tasks():
    user = User.from_session(db, session)
    stats = user.get_stats()
    test_path = stats.get("test_path", {})
    tasks = _generate_ai_tasks(test_path.get("strengths", ""), test_path.get("weaknesses", ""))
    return jsonify(tasks)


@app.route("/dashboard/test-path-status")
@login_required
def test_path_status():
    user = User.from_session(db, session)
    stats = user.get_stats()
    test_path = stats.get("test_path", {})
    # Check if any field in test_path is filled
    has_path = any(test_path.get(k) for k in [
                   "desired_sat", "desired_act", "strengths", "weaknesses", "test_date", "test_time"])
    return jsonify({"has_path": has_path})

# Logout


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))


@app.route('/dashboard/college-path-builder')
@login_required
def college_path_builder():
    return render_template('college_path_builder.html')


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
