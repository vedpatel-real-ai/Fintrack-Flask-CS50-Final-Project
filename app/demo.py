"""
Demo workspace.

Recruiters shouldn't have to register an account to evaluate this
project. Clicking "Try Demo" logs into a fixed demo account that is
wiped and reseeded with realistic data every time it's entered, so it
always looks the way it's meant to look -- no stale or vandalized data
from a previous visitor, and no scheduled job required to reset it.
"""

import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

from app.extensions import db

DEMO_USERNAME = "demo"
DEMO_FRIEND_USERNAME = "demo_friend"
# Demo accounts are reseeded on every visit, so the password is not a
# real secret -- it's only ever reached through the "Try Demo" button.
DEMO_PASSWORD_HASH = generate_password_hash("demo-workspace")

CATEGORIES = [
    "Groceries", "Rent", "Utilities", "Transportation",
    "Dining Out", "Entertainment", "Healthcare", "Shopping",
]

EXPENSE_TITLES = {
    "Groceries": ["Weekly groceries", "Farmers market", "Supermarket run"],
    "Rent": ["Monthly rent"],
    "Utilities": ["Electricity bill", "Internet bill", "Water bill"],
    "Transportation": ["Gas", "Metro pass", "Rideshare"],
    "Dining Out": ["Lunch with coworkers", "Dinner out", "Coffee shop"],
    "Entertainment": ["Movie night", "Concert tickets", "Streaming subscription"],
    "Healthcare": ["Pharmacy", "Doctor visit copay", "Gym membership"],
    "Shopping": ["New shoes", "Home supplies", "Electronics accessory"],
}

BUDGETS = {
    "Groceries": 450, "Rent": 1400, "Utilities": 200,
    "Transportation": 150, "Dining Out": 180, "Entertainment": 100,
    "Healthcare": 120, "Shopping": 150,
}


def _get_or_create_user(username, currency="USD"):
    existing = db.execute("SELECT id FROM users WHERE username = ?", username)
    if existing:
        return existing[0]["id"]

    return db.execute(
        "INSERT INTO users (username, password, currency, is_demo) VALUES (?, ?, ?, 1)",
        username, DEMO_PASSWORD_HASH, currency,
    )


def _wipe_user_data(user_id):
    for table in (
        "shared_expenses", "notifications", "recurring_expenses",
        "budget", "income", "expenses", "categories",
    ):
        column = "owner_id" if table == "shared_expenses" else "user_id"
        db.execute(f"DELETE FROM {table} WHERE {column} = ?", user_id)
    db.execute("DELETE FROM shared_expenses WHERE shared_with_id = ?", user_id)


def reset_demo_workspace():
    """Wipe and reseed the demo account. Returns the demo user's id."""

    demo_user_id = _get_or_create_user(DEMO_USERNAME)
    friend_id = _get_or_create_user(DEMO_FRIEND_USERNAME)

    _wipe_user_data(demo_user_id)
    _wipe_user_data(friend_id)

    for category in CATEGORIES:
        db.execute(
            "INSERT INTO categories (user_id, category_name) VALUES (?, ?)",
            demo_user_id, category,
        )
        db.execute(
            "INSERT INTO budget (user_id, category, monthly_budget) VALUES (?, ?, ?)",
            demo_user_id, category, BUDGETS[category],
        )

    today = datetime.now()
    rng = random.Random(42)  # fixed seed -> same believable demo every time

    for days_ago in range(0, 90):
        date = today - timedelta(days=days_ago)
        # A handful of transactions a week, not every single day.
        if rng.random() > 0.35:
            continue
        category = rng.choice(CATEGORIES)
        title = rng.choice(EXPENSE_TITLES[category])
        amount = round(rng.uniform(8, 120), 2)
        db.execute(
            "INSERT INTO expenses (user_id, title, amount, date, category) VALUES (?, ?, ?, ?, ?)",
            demo_user_id, title, amount, date.strftime("%Y-%m-%d"), category,
        )

    # A rent payment near the start of each of the last three months.
    for months_back in range(3):
        date = (today.replace(day=1) - timedelta(days=months_back * 30))
        db.execute(
            "INSERT INTO expenses (user_id, title, amount, date, category) VALUES (?, ?, ?, ?, ?)",
            demo_user_id, "Monthly rent", BUDGETS["Rent"], date.strftime("%Y-%m-%d"), "Rent",
        )

    db.execute(
        "INSERT INTO recurring_expenses (user_id, title, amount, category, start_date, frequency) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        demo_user_id, "Streaming subscription", 15.99, "Entertainment",
        today.strftime("%Y-%m-%d"), "monthly",
    )
    db.execute(
        "INSERT INTO recurring_expenses (user_id, title, amount, category, start_date, frequency) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        demo_user_id, "Gym membership", 39.00, "Healthcare",
        today.strftime("%Y-%m-%d"), "monthly",
    )

    for source, amount, days_ago in [
        ("Monthly salary", 4200.00, 3),
        ("Freelance project", 650.00, 18),
        ("Monthly salary", 4200.00, 33),
    ]:
        date = today - timedelta(days=days_ago)
        db.execute(
            "INSERT INTO income (user_id, amount, source, date, category) VALUES (?, ?, ?, ?, ?)",
            demo_user_id, amount, source, date.strftime("%Y-%m-%d"), "Income",
        )

    db.execute(
        "INSERT INTO notifications (user_id, message) VALUES (?, ?)",
        demo_user_id, "Your budget for Dining Out is close to its monthly limit.",
    )
    db.execute(
        "INSERT INTO notifications (user_id, message) VALUES (?, ?)",
        demo_user_id, "New recurring expense added: Streaming subscription.",
    )

    # Share one expense from the friend account so the sharing feature
    # has something real to show without extra clicks.
    shared_expense_id = db.execute(
        "INSERT INTO expenses (user_id, title, amount, date, category) VALUES (?, ?, ?, ?, ?)",
        friend_id, "Shared apartment cleaning", 60.00, today.strftime("%Y-%m-%d"), "Shopping",
    )
    db.execute(
        "INSERT INTO shared_expenses (owner_id, shared_with_id, expense_id) VALUES (?, ?, ?)",
        friend_id, demo_user_id, shared_expense_id,
    )
    db.execute(
        "INSERT INTO notifications (user_id, message) VALUES (?, ?)",
        demo_user_id, "Expense shared by demo_friend. Check your shared expenses.",
    )

    return demo_user_id
