"""
Application factory for FinTrack.

Using a factory (instead of a single global `app = Flask(__name__)` in
app.py) is a small, well-known Flask pattern that keeps configuration,
extension setup, and route registration cleanly separated. Routes are
grouped into blueprints under app/routes/ by feature area.
"""

import os
import secrets
import sqlite3
import warnings

from flask import Flask, render_template, session

from config import get_config
from app.extensions import csrf, init_db


def create_app():
    app = Flask(__name__)
    app.config.from_object(get_config())

    _configure_secret_key(app)
    _ensure_instance_folder(app)
    _init_database(app)

    csrf.init_app(app)

    _register_blueprints(app)
    _register_error_handlers(app)
    _register_template_helpers(app)

    return app


def _configure_secret_key(app):
    """
    Require SECRET_KEY in production; generate a temporary one for local
    dev so the app still boots, but warn loudly so it's never mistaken
    for a real secret.
    """
    if app.config["SECRET_KEY"]:
        return

    if not app.debug:
        raise RuntimeError(
            "SECRET_KEY environment variable is not set. "
            "Set it before running in production (see .env.example)."
        )

    warnings.warn(
        "SECRET_KEY is not set -- using a random throwaway key for this "
        "process only. Sessions will not survive a restart. "
        "Copy .env.example to .env and set SECRET_KEY for real use.",
        stacklevel=2,
    )
    app.config["SECRET_KEY"] = secrets.token_hex(32)


def _ensure_instance_folder(app):
    instance_dir = os.path.dirname(app.config["DATABASE_PATH"])
    os.makedirs(instance_dir, exist_ok=True)


def _init_database(app):
    database_path = app.config["DATABASE_PATH"]
    database_exists = os.path.exists(database_path)

    if not database_exists:
        open(database_path, "a").close()

    # Apply schema.sql with plain sqlite3 (executescript isn't part of the
    # cs50 SQL wrapper's API). This only ever runs CREATE TABLE/INDEX IF
    # NOT EXISTS statements, so it's safe on every startup and never
    # touches existing data.
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r") as schema_file:
        schema_sql = schema_file.read()

    connection = sqlite3.connect(database_path)
    connection.executescript(schema_sql)
    connection.commit()
    connection.close()

    init_db(f"sqlite:///{database_path}")


def _register_blueprints(app):
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.expenses import expenses_bp
    from app.routes.income import income_bp
    from app.routes.budgets import budgets_bp
    from app.routes.recurring import recurring_bp
    from app.routes.categories import categories_bp
    from app.routes.notifications import notifications_bp
    from app.routes.reports import reports_bp
    from app.routes.settings import settings_bp
    from app.routes.profile import profile_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(income_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(recurring_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(profile_bp)


def _register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("errors/500.html"), 500

    @app.errorhandler(413)
    def file_too_large(error):
        return render_template("errors/500.html", message="That file is too large."), 413


def _register_template_helpers(app):
    """Small helpers every template needs, without repeating them per-route."""

    @app.context_processor
    def inject_globals():
        return {
            "is_demo": session.get("is_demo", False),
        }

    @app.template_filter("format_currency")
    def format_currency(amount, currency="USD"):
        symbols = {"USD": "$", "EUR": "\u20ac", "GBP": "\u00a3", "JPY": "\u00a5", "INR": "\u20b9"}
        symbol = symbols.get(currency, "")
        try:
            return f"{symbol}{float(amount):,.2f}"
        except (TypeError, ValueError):
            return f"{symbol}0.00"
