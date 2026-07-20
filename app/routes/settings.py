"""User preferences: currency and theme."""

from flask import Blueprint, render_template, request, redirect, session, url_for, flash

from app.extensions import db
from app.utils.decorators import login_required
from app.utils.currency import SUPPORTED_CURRENCIES

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings", methods=["GET", "POST"])
@login_required
def index():
    user_id = session["user_id"]
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.login"))
    user = user[0]

    return render_template(
        "settings.html", user=user, currency=session.get("currency", "USD"),
        theme=session.get("theme", "light"), currencies=SUPPORTED_CURRENCIES,
    )


@settings_bp.route("/set_currency", methods=["POST"])
@login_required
def set_currency():
    user_id = session["user_id"]
    currency = request.form.get("currency", "USD")

    if currency not in SUPPORTED_CURRENCIES:
        flash("Unsupported currency.", "danger")
        return redirect(url_for("settings.index"))

    session["currency"] = currency
    db.execute("UPDATE users SET currency = ? WHERE id = ?", currency, user_id)
    flash(f"Currency set to {currency}.", "success")
    return redirect(url_for("dashboard.index"))
