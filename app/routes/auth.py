"""Authentication: register, login, logout, and the one-click demo."""

from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db
from app.demo import reset_demo_workspace, DEMO_USERNAME

auth_bp = Blueprint("auth", __name__)

MIN_PASSWORD_LENGTH = 8


@auth_bp.route("/")
def index():
    """Landing page: redirect straight to the dashboard if already logged in."""
    if "user_id" in session:
        return redirect(url_for("dashboard.index"))
    return render_template("index.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Create a new account. Validates the username/password, hashes the
    password with Werkzeug, and stores the new user.
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        error = _validate_registration(username, password, confirm_password)
        if error:
            flash(error, "danger")
            return render_template("register.html", username=username)

        existing_user = db.execute("SELECT id FROM users WHERE username = ?", username)
        if existing_user:
            flash("That username is already taken.", "danger")
            return render_template("register.html", username=username)

        hashed_password = generate_password_hash(password)
        user_id = db.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)", username, hashed_password
        )

        session.clear()
        session["user_id"] = user_id
        session["username"] = username
        flash(f"Welcome to FinTrack, {username}!", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("register.html")


def _validate_registration(username, password, confirm_password):
    if not username or not password:
        return "Username and password are both required."
    if len(username) < 3:
        return "Username must be at least 3 characters long."
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
    if password != confirm_password:
        return "Passwords do not match."
    return None


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Check the submitted credentials and start a session if they're valid."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember_me = request.form.get("remember_me")

        users = db.execute("SELECT * FROM users WHERE username = ?", username)
        user = users[0] if users else None

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["is_demo"] = bool(user["is_demo"])
            session["currency"] = user["currency"]
            session.permanent = bool(remember_me)
            return redirect(url_for("dashboard.index"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@auth_bp.route("/demo")
def demo():
    """One click, no registration: log straight into a freshly seeded demo account."""
    demo_user_id = reset_demo_workspace()

    session.clear()
    session["user_id"] = demo_user_id
    session["username"] = DEMO_USERNAME
    session["is_demo"] = True
    session["currency"] = "USD"

    flash("You're exploring a demo workspace with sample data.", "info")
    return redirect(url_for("dashboard.index"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.index"))
