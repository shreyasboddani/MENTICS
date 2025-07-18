from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from dbhelper import DatabaseHandler

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for session management

db = DatabaseHandler("users.db")

# Create database and user table if it doesn't exist
def init_db():
    db.create_table("users", {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "email": "TEXT NOT NULL UNIQUE",
        "password": "TEXT NOT NULL"
    })

# Home page
@app.route("/")
def home():
    return render_template("index.html")

# Signup route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        try:
            db.insert("users", {"email": email, "password": password})
            return redirect(url_for("login"))
        except Exception:
            return "Email already exists!"
    return render_template("signup.html")

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = db.select("users", where={"email": email})
        if user and check_password_hash(user[0][2], password):
            session["user"] = user[0][1]
            return redirect(url_for("dashboard"))
        else:
            return "Invalid credentials"
    return render_template("login.html")

# Dashboard page
@app.route("/dashboard")
def dashboard():
    if "user" in session:
        return render_template("dashboard.html")
    return redirect(url_for("login"))

@app.route("/dashboard/stats")
def stats():
    if "user" in session:
        return render_template("stats.html")
    return redirect(url_for("login"))

@app.route("/dashboard/builder")
def builder():
    if "user" in session:
        return render_template("builder.html")
    return redirect(url_for("login"))

@app.route("/dashboard/tracker")
def tracker():
    if "user" in session:
        return render_template("tracker.html")
    return redirect(url_for("login"))

# Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
