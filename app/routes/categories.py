"""User-defined expense/income categories."""

from flask import Blueprint, request, redirect, session, url_for, flash

from app.extensions import db
from app.utils.decorators import login_required

categories_bp = Blueprint("categories", __name__)


@categories_bp.route("/add_category", methods=["POST"])
@login_required
def add_category():
    user_id = session["user_id"]
    category_name = request.form.get("category", "").strip()

    if category_name:
        existing = db.execute(
            "SELECT id FROM categories WHERE user_id = ? AND category_name = ?", user_id, category_name
        )
        if not existing:
            db.execute(
                "INSERT INTO categories (user_id, category_name) VALUES (?, ?)", user_id, category_name
            )
            flash(f"Category '{category_name}' added.", "success")

    next_url = request.referrer or url_for("dashboard.index")
    return redirect(next_url)
