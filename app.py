from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from dbhelper import DatabaseHandler
from userhelper import User
from functools import wraps
import json

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for session management
app.url_map.strict_slashes = False

db = DatabaseHandler("users.db")

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
            db.insert("users", {"email": email, "password": password,
                      "stats": '{"sat": "0", "act": "0", "gpa": "0.0"}'})
            return redirect(url_for("login"))
        except Exception as e:
            print(f"Signup error: {e}")  # for debugging in terminal
            error = "Email already exists!"  # or a more generic message
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
    return render_template("dashboard.html")


@app.route("/dashboard/stats", methods=["GET"])
@login_required
def stats():
    user = User.from_session(db, session)
    if not user:
        return redirect(url_for("login"))

    stats = user.get_stats()
    return render_template("stats.html", sat=stats["sat"], act=stats["act"], gpa=stats["gpa"])


@app.route("/dashboard/stats/edit", methods=["GET", "POST"])
@login_required
def edit_stats():
    user = User.from_session(db, session)
    if not user:
        return redirect(url_for("login"))
    stats = user.get_stats()
    error = None
    if request.method == "POST":
        sat = request.form.get("sat", "")
        act = request.form.get("act", "")
        gpa = request.form.get("gpa", "")
        try:
            stats["sat"] = sat
            stats["act"] = act
            stats["gpa"] = gpa
            user.set_stats(stats)
            return redirect(url_for("stats"))
        except Exception as e:
            print("Error updating stats:", e)  # <--- Add this line
            error = "Could not update stats."
    return render_template("edit_stats.html", sat=stats.get("sat", ""), act=stats.get("act", ""), gpa=stats.get("gpa", ""), error=error)


@app.route("/dashboard/builder")
@login_required
def builder():
    return render_template("builder.html")


@app.route("/dashboard/tracker")
@login_required
def tracker():
    return render_template("tracker.html")


@app.route("/dashboard/test-path-builder")
@login_required
def test_path_builder():
    return render_template("test_path_builder.html")


@app.route("/dashboard/college-path-builder")
@login_required
def college_path_builder():
    return render_template("college_path_builder.html")

# Logout


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
