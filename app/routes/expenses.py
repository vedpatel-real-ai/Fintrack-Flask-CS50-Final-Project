"""Expense CRUD, filtering/sorting/pagination, CSV import/export, sharing."""

from io import BytesIO

import pandas as pd
from flask import Blueprint, render_template, request, redirect, session, url_for, flash, send_file

from app.extensions import db
from app.utils.decorators import login_required
from app.utils.currency import get_exchange_rates, get_conversion_rate

expenses_bp = Blueprint("expenses", __name__)

PER_PAGE = 10
SORTABLE_COLUMNS = {"date", "amount", "category", "title"}


@expenses_bp.route("/add_expense", methods=["GET", "POST"])
@login_required
def add_expense():
    user_id = session["user_id"]

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        amount_raw = request.form.get("amount", "")
        date = request.form.get("date", "")
        new_category = request.form.get("new_category", "").strip()
        selected_category = request.form.get("category", "")
        category = new_category or selected_category
        currency = request.form.get("currency", "USD")
        is_recurring = "recurring" in request.form
        frequency = request.form.get("frequency") if is_recurring else None

        try:
            amount = float(amount_raw)
        except ValueError:
            amount = 0

        if not title or not date or not category or amount <= 0:
            flash("All fields are required and the amount must be greater than 0.", "danger")
            return redirect(url_for("expenses.add_expense"))

        default_currency = session.get("currency", "USD")
        converted_amount = amount * get_conversion_rate(currency, default_currency)

        if new_category:
            _ensure_category(user_id, new_category)

        if is_recurring:
            db.execute(
                "INSERT INTO recurring_expenses (user_id, title, amount, category, start_date, frequency) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                user_id, title, converted_amount, category, date, frequency,
            )
        else:
            db.execute(
                "INSERT INTO expenses (user_id, title, amount, date, category) VALUES (?, ?, ?, ?, ?)",
                user_id, title, converted_amount, date, category,
            )
            _check_budget(user_id, category, date)

        flash("Expense added successfully!", "success")
        return redirect(url_for("expenses.view_expenses"))

    categories = _user_categories(user_id)
    return render_template(
        "add_expense.html", categories=categories, selected_currency=session.get("currency", "USD")
    )


def _ensure_category(user_id, category_name):
    existing = db.execute(
        "SELECT id FROM categories WHERE user_id = ? AND category_name = ?", user_id, category_name
    )
    if not existing:
        db.execute(
            "INSERT INTO categories (user_id, category_name) VALUES (?, ?)", user_id, category_name
        )


def _user_categories(user_id):
    rows = db.execute(
        "SELECT category_name FROM categories WHERE user_id = ? ORDER BY category_name", user_id
    )
    return [row["category_name"] for row in rows]


def _check_budget(user_id, category, date):
    current_month = date[:7]
    total = db.execute(
        """
        SELECT SUM(amount) AS total FROM expenses
        WHERE user_id = ? AND category = ? AND strftime('%Y-%m', date) = ?
        """,
        user_id, category, current_month,
    )[0]["total"] or 0.0

    budgets = db.execute(
        "SELECT monthly_budget FROM budget WHERE user_id = ? AND category = ?", user_id, category
    )
    if budgets and total > float(budgets[0]["monthly_budget"]):
        limit = budgets[0]["monthly_budget"]
        flash(f"Budget for {category} exceeded (limit {limit}, spent {total:.2f}).", "warning")
        db.execute(
            "INSERT INTO notifications (user_id, message) VALUES (?, ?)",
            user_id,
            f"Your budget for {category} has been exceeded. Limit: {limit}, spent: {total:.2f}.",
        )


@expenses_bp.route("/view_expenses", methods=["GET", "POST"])
@login_required
def view_expenses():
    user_id = session["user_id"]

    category = request.values.get("category", "All")
    start_date = request.values.get("start_date", "")
    end_date = request.values.get("end_date", "")
    sort_by = request.values.get("sort_by", "date")
    search = request.values.get("search", "").strip()
    page = max(1, request.values.get("page", 1, type=int))

    if sort_by not in SORTABLE_COLUMNS:
        sort_by = "date"

    query = "SELECT *, 'Not Recurring' AS is_recurring FROM expenses WHERE user_id = ?"
    params = [user_id]

    if category != "All":
        query += " AND category = ?"
        params.append(category)
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")

    all_expenses = db.execute(query, *params)

    currency = session.get("currency", "USD")
    rates = get_exchange_rates("USD")
    conversion_rate = rates.get(currency, 1)

    combined = []
    for expense in all_expenses:
        combined.append({
            "id": expense["id"],
            "title": expense["title"],
            "converted_amount": expense["amount"] * conversion_rate,
            "date": expense["date"],
            "category": expense["category"],
            "is_recurring": "Not Recurring",
        })

    reverse = sort_by != "title"
    combined.sort(key=lambda item: item[sort_by if sort_by != "amount" else "converted_amount"], reverse=reverse)

    total_count = len(combined)
    total_pages = max(1, (total_count + PER_PAGE - 1) // PER_PAGE)
    page = min(page, total_pages)
    start = (page - 1) * PER_PAGE
    page_items = combined[start:start + PER_PAGE]

    categories = _user_categories(user_id)

    return render_template(
        "view_expenses.html",
        expenses=page_items,
        categories=categories,
        selected_currency=currency,
        filters={
            "category": category, "start_date": start_date,
            "end_date": end_date, "sort_by": sort_by, "search": search,
        },
        page=page,
        total_pages=total_pages,
        total_count=total_count,
    )


@expenses_bp.route("/delete_expense/<int:expense_id>", methods=["POST"])
@login_required
def delete_expense(expense_id):
    user_id = session["user_id"]

    deleted = db.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", expense_id, user_id)
    if not deleted:
        deleted = db.execute(
            "DELETE FROM recurring_expenses WHERE id = ? AND user_id = ?", expense_id, user_id
        )

    if deleted:
        flash("Expense deleted successfully.", "success")
    else:
        flash("Expense not found or you don't have permission to delete it.", "danger")

    return redirect(url_for("expenses.view_expenses"))


@expenses_bp.route("/import_expenses", methods=["GET", "POST"])
@login_required
def import_expenses():
    user_id = session["user_id"]

    if request.method == "POST":
        uploaded_file = request.files.get("file")

        if not uploaded_file or not uploaded_file.filename.endswith(".csv"):
            flash("Please upload a valid CSV file.", "danger")
            return redirect(url_for("expenses.import_expenses"))

        try:
            data_frame = pd.read_csv(uploaded_file)
        except Exception:
            flash("Couldn't read that file. Make sure it's a valid CSV.", "danger")
            return redirect(url_for("expenses.import_expenses"))

        required_columns = {"title", "amount", "date", "category"}
        if not required_columns.issubset(set(data_frame.columns.str.lower())):
            flash("CSV must include title, amount, date, and category columns.", "danger")
            return redirect(url_for("expenses.import_expenses"))

        data_frame.columns = data_frame.columns.str.lower()
        imported = 0
        for _, row in data_frame.iterrows():
            is_recurring = str(row.get("recurring", "")).strip().lower() == "recurring"
            try:
                amount = float(row["amount"])
            except (ValueError, TypeError):
                continue

            if is_recurring:
                frequency = row.get("frequency", "monthly") or "monthly"
                db.execute(
                    "INSERT INTO recurring_expenses (user_id, title, amount, start_date, category, frequency) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    user_id, row["title"], amount, row["date"], row["category"], frequency,
                )
            else:
                db.execute(
                    "INSERT INTO expenses (user_id, title, amount, date, category) VALUES (?, ?, ?, ?, ?)",
                    user_id, row["title"], amount, row["date"], row["category"],
                )
            imported += 1

        flash(f"Imported {imported} expense(s) successfully!", "success")
        return redirect(url_for("expenses.view_expenses"))

    return render_template("import_expenses.html")


@expenses_bp.route("/export_expenses")
@login_required
def export_expenses():
    user_id = session["user_id"]
    expenses = db.execute(
        """
        SELECT id, amount, title, date, category, 'Not recurring' AS recurring FROM expenses WHERE user_id = ?
        UNION ALL
        SELECT id, amount, title, start_date AS date, category, 'Recurring' AS recurring
        FROM recurring_expenses WHERE user_id = ?
        """,
        user_id, user_id,
    )

    data_frame = pd.DataFrame(expenses)
    buffer = BytesIO()
    data_frame.to_csv(buffer, index=False)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="expenses.csv", mimetype="text/csv")


@expenses_bp.route("/share_expense/<int:expense_id>", methods=["GET", "POST"])
@login_required
def share_expense(expense_id):
    if request.method == "POST":
        shared_with_username = request.form.get("shared_with", "").strip()
        recipients = db.execute("SELECT id FROM users WHERE username = ?", shared_with_username)

        if not recipients:
            flash("User not found.", "danger")
            return redirect(url_for("expenses.view_expenses"))

        shared_with_id = recipients[0]["id"]
        owner_id = session["user_id"]

        if shared_with_id == owner_id:
            flash("You can't share an expense with yourself.", "danger")
            return redirect(url_for("expenses.view_expenses"))

        db.execute(
            "INSERT INTO shared_expenses (owner_id, shared_with_id, expense_id) VALUES (?, ?, ?)",
            owner_id, shared_with_id, expense_id,
        )

        owner = db.execute("SELECT username FROM users WHERE id = ?", owner_id)[0]
        db.execute(
            "INSERT INTO notifications (user_id, message) VALUES (?, ?)",
            shared_with_id, f"Expense shared by {owner['username']}. Check your shared expenses.",
        )

        flash("Expense shared successfully!", "success")
        return redirect(url_for("expenses.view_expenses"))

    return render_template("share_expense.html", expense_id=expense_id)


@expenses_bp.route("/view_shared_expenses")
@login_required
def view_shared_expenses():
    user_id = session["user_id"]
    shared_expenses = db.execute(
        """
        SELECT e.*, u.username AS owner_username
        FROM expenses e
        JOIN shared_expenses se ON e.id = se.expense_id
        JOIN users u ON se.owner_id = u.id
        WHERE se.shared_with_id = ?
        ORDER BY e.date DESC
        """,
        user_id,
    )
    return render_template("view_shared_expenses.html", shared_expenses=shared_expenses)
