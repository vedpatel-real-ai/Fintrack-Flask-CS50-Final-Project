"""Recurring expenses."""

from flask import Blueprint, render_template, request, redirect, session, url_for, flash

from app.extensions import db
from app.utils.decorators import login_required

recurring_bp = Blueprint("recurring", __name__)


@recurring_bp.route("/add_recurring_expense", methods=["GET", "POST"])
@login_required
def add_recurring_expense():
    user_id = session["user_id"]

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        amount_raw = request.form.get("amount", "")
        category = request.form.get("category", "").strip()
        start_date = request.form.get("start_date", "")
        frequency = request.form.get("frequency", "")

        try:
            amount = float(amount_raw)
        except ValueError:
            amount = 0

        if not title or amount <= 0 or not category or not start_date or not frequency:
            flash("All fields are required and the amount must be greater than 0.", "danger")
            return redirect(url_for("recurring.add_recurring_expense"))

        db.execute(
            "INSERT INTO recurring_expenses (user_id, title, amount, category, start_date, frequency) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            user_id, title, amount, category, start_date, frequency,
        )

        flash("Recurring expense added successfully!", "success")
        return redirect(url_for("recurring.view_recurring_expenses"))

    return render_template("add_recurring_expense.html")


@recurring_bp.route("/view_recurring_expenses")
@login_required
def view_recurring_expenses():
    user_id = session["user_id"]
    recurring_expenses = db.execute("SELECT * FROM recurring_expenses WHERE user_id = ?", user_id)
    return render_template("view_recurring_expenses.html", recurring_expenses=recurring_expenses)


@recurring_bp.route("/delete_recurring_expense/<int:expense_id>", methods=["POST"])
@login_required
def delete_recurring_expense(expense_id):
    user_id = session["user_id"]
    db.execute("DELETE FROM recurring_expenses WHERE id = ? AND user_id = ?", expense_id, user_id)
    flash("Recurring expense deleted successfully!", "success")
    return redirect(url_for("recurring.view_recurring_expenses"))
