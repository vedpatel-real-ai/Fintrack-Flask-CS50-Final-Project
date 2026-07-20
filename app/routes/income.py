"""Income entries: add, list, delete."""

from flask import Blueprint, render_template, request, redirect, session, url_for, flash

from app.extensions import db
from app.utils.decorators import login_required
from app.utils.currency import get_exchange_rates, get_conversion_rate

income_bp = Blueprint("income", __name__)


def _user_categories(user_id):
    rows = db.execute(
        "SELECT category_name FROM categories WHERE user_id = ? ORDER BY category_name", user_id
    )
    return [row["category_name"] for row in rows]


@income_bp.route("/add_income", methods=["GET", "POST"])
@login_required
def add_income():
    user_id = session["user_id"]

    if request.method == "POST":
        amount_raw = request.form.get("amount", "")
        source = request.form.get("source", "").strip()
        date = request.form.get("date", "")
        input_currency = request.form.get("currency", "USD")
        new_category = request.form.get("new_category", "").strip()
        selected_category = request.form.get("category", "")
        category = new_category or selected_category

        try:
            amount = float(amount_raw)
        except ValueError:
            amount = 0

        if not source or not date or not category or amount <= 0:
            flash("All fields are required and the amount must be greater than 0.", "danger")
            return redirect(url_for("income.add_income"))

        default_currency = session.get("currency", "USD")
        converted_amount = amount * get_conversion_rate(input_currency, default_currency)

        if new_category:
            existing = db.execute(
                "SELECT id FROM categories WHERE user_id = ? AND category_name = ?", user_id, new_category
            )
            if not existing:
                db.execute(
                    "INSERT INTO categories (user_id, category_name) VALUES (?, ?)", user_id, new_category
                )

        db.execute(
            "INSERT INTO income (user_id, amount, source, date, category) VALUES (?, ?, ?, ?, ?)",
            user_id, converted_amount, source, date, category,
        )

        flash("Income added successfully!", "success")
        return redirect(url_for("income.view_income"))

    return render_template(
        "add_income.html", selected_currency=session.get("currency", "USD"),
        categories=_user_categories(user_id),
    )


@income_bp.route("/view_income")
@login_required
def view_income():
    user_id = session["user_id"]
    selected_currency = session.get("currency", "USD")

    income_entries = db.execute("SELECT * FROM income WHERE user_id = ? ORDER BY date DESC", user_id)

    rates = get_exchange_rates("USD")
    conversion_rate = rates.get(selected_currency, 1)

    converted_entries = []
    total = 0
    for entry in income_entries:
        converted_amount = entry["amount"] * conversion_rate
        total += converted_amount
        converted_entries.append({**entry, "converted_amount": converted_amount})

    return render_template(
        "view_income.html", income_entries=converted_entries,
        selected_currency=selected_currency, total_income=total,
    )


@income_bp.route("/delete_income/<int:income_id>", methods=["POST"])
@login_required
def delete_income(income_id):
    user_id = session["user_id"]
    deleted = db.execute("DELETE FROM income WHERE id = ? AND user_id = ?", income_id, user_id)
    if deleted:
        flash("Income entry deleted.", "success")
    else:
        flash("Income entry not found.", "danger")
    return redirect(url_for("income.view_income"))
