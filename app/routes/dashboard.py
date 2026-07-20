"""Main dashboard: financial overview, recent activity, notifications."""

from datetime import datetime

from flask import Blueprint, render_template, session

from app.extensions import db
from app.utils.decorators import login_required
from app.utils.currency import get_exchange_rates

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def index():
    user_id = session["user_id"]
    users = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    if not users:
        session.clear()
        return render_template("errors/404.html"), 404
    user = users[0]

    currency = session.get("currency", "USD")
    rates = get_exchange_rates("USD")
    conversion_rate = rates.get(currency, 1)

    total_income = db.execute(
        "SELECT SUM(amount) AS total FROM income WHERE user_id = ?", user_id
    )[0]["total"] or 0
    total_expenses = db.execute(
        "SELECT SUM(amount) AS total FROM expenses WHERE user_id = ?", user_id
    )[0]["total"] or 0

    recent_expenses = db.execute(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC LIMIT 5", user_id
    )
    notifications = db.execute(
        "SELECT * FROM notifications WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5", user_id
    )

    top_categories = db.execute(
        """
        SELECT category, SUM(amount) AS total
        FROM expenses
        WHERE user_id = ?
        GROUP BY category
        ORDER BY total DESC
        LIMIT 5
        """,
        user_id,
    )

    budgets = db.execute(
        """
        SELECT category, monthly_budget FROM budget WHERE user_id = ?
        """,
        user_id,
    )
    current_month = datetime.now().strftime("%Y-%m")
    budget_progress = []
    for budget in budgets:
        spent = db.execute(
            """
            SELECT SUM(amount) AS total FROM expenses
            WHERE user_id = ? AND category = ? AND strftime('%Y-%m', date) = ?
            """,
            user_id, budget["category"], current_month,
        )[0]["total"] or 0
        percent = min(100, round((spent / budget["monthly_budget"]) * 100)) if budget["monthly_budget"] else 0
        budget_progress.append({
            "category": budget["category"],
            "spent": spent,
            "limit": budget["monthly_budget"],
            "percent": percent,
        })

    return render_template(
        "dashboard.html",
        user=user,
        expenses=recent_expenses,
        notifications=notifications,
        total_income=total_income * conversion_rate,
        total_expenses=total_expenses * conversion_rate,
        net_balance=(total_income - total_expenses) * conversion_rate,
        currency=currency,
        top_categories=top_categories,
        budget_progress=budget_progress,
    )
