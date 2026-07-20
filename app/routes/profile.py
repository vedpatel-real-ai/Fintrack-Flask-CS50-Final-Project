"""Account profile: update username/password."""

from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.utils.decorators import login_required

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile", methods=["GET", "POST"])
@login_required
def index():
    user_id = session["user_id"]
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.login"))
    user = user[0]

    if request.method == "POST":
        if user["is_demo"]:
            flash("Profile changes are disabled in the demo workspace.", "info")
            return redirect(url_for("profile.index"))

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Both username and password are required.", "danger")
            return redirect(url_for("profile.index"))

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return redirect(url_for("profile.index"))

        existing = db.execute(
            "SELECT id FROM users WHERE username = ? AND id != ?", username, user_id
        )
        if existing:
            flash("Username already exists. Please choose a different one.", "danger")
            return redirect(url_for("profile.index"))

        hashed_password = generate_password_hash(password)
        db.execute(
            "UPDATE users SET username = ?, password = ? WHERE id = ?", username, hashed_password, user_id
        )
        session["username"] = username
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile.index"))

    return render_template("profile.html", user=user)
