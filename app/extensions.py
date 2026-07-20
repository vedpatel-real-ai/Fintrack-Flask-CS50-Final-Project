"""
Extension instances live here so any module can import them without
triggering circular imports with the app factory in app/__init__.py.
"""

from cs50 import SQL
from flask_wtf import CSRFProtect

csrf = CSRFProtect()

# The cs50 SQL wrapper is initialized lazily inside create_app() once we
# know the database path, then attached to this module-level name so the
# rest of the app can simply `from app.extensions import db`.
db = None


def init_db(database_uri):
    global db
    db = SQL(database_uri)
    return db
