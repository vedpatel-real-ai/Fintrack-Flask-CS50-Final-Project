"""Monthly budgets per category."""

from datetime import datetime

from flask import Blueprint, render_template, request, redirect, session, url_for, flash

from app.extensions import db
from app.utils.decorators import login_required

budgets_bp = Blueprint("budgets", __name__)


@budgets_bp.route("/set_budget", methods=["GET", "POST"])
@login_required
def set_budget():
    user_id = session["user_id"]
    categories = db.execute(
        "SELECT category_name FROM categories WHERE user_id = ? ORDER BY category_name", user_id
    )

    if request.method == "POST":
        new_category = request.form.get("new_category", "").strip()
        selected_category = request.form.get("category", "")
        monthly_budget_raw = request.form.get("monthly_budget", "")

        if not new_category and not selected_category:
            flash("Please either type a new category or select an existing one.", "danger")
            return redirect(url_for("budgets.set_budget"))

        try:
            monthly_budget = float(monthly_budget_raw)
            if monthly_budget <= 0:
                raise ValueError
        except ValueError:
            flash("Monthly budget must be a positive number.", "danger")
            return redirect(url_for("budgets.set_budget"))

        category = new_category or selected_category

        if new_category:
            existing = db.execute(
                "SELECT id FROM categories WHERE user_id = ? AND category_name = ?", user_id, new_category
            )
            if not existing:
                db.execute(
                    "INSERT INTO categories (user_id, category_name) VALUES (?, ?)", user_id, new_category
                )

        existing_budget = db.execute(
            "SELECT id FROM budget WHERE user_id = ? AND category = ?", user_id, category
        )
        if existing_budget:
            db.execute(
                "UPDATE budget SET monthly_budget = ? WHERE user_id = ? AND category = ?",
                monthly_budget, user_id, category,
            )
        else:
            db.execute(
                "INSERT INTO budget (user_id, category, monthly_budget) VALUES (?, ?, ?)",
                user_id, category, monthly_budget,
            )

        flash("Budget set successfully!", "success")
        return redirect(url_for("budgets.view_budgets"))

    return render_template("set_budget.html", categories=categories)


@budgets_bp.route("/view_budgets")
@login_required
def view_budgets():
    user_id = session["user_id"]
    budgets = db.execute("SELECT * FROM budget WHERE user_id = ?", user_id)

    current_month = datetime.now().strftime("%Y-%m")
    enriched = []
    for budget in budgets:
        spent = db.execute(
            """
            SELECT SUM(amount) AS total FROM expenses
            WHERE user_id = ? AND category = ? AND strftime('%Y-%m', date) = ?
            """,
            user_id, budget["category"], current_month,
        )[0]["total"] or 0
        percent = min(100, round((spent / budget["monthly_budget"]) * 100)) if budget["monthly_budget"] else 0
        enriched.append({**budget, "spent": spent, "percent": percent})

    return render_template("view_budget.html", budgets=enriched)


@budgets_bp.route("/delete_budget/<int:budget_id>", methods=["POST"])
@login_required
def delete_budget(budget_id):
    user_id = session["user_id"]
    db.execute("DELETE FROM budget WHERE id = ? AND user_id = ?", budget_id, user_id)
    flash("Budget deleted successfully!", "success")
    return redirect(url_for("budgets.view_budgets"))
