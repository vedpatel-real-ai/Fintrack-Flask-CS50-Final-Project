"""
Application configuration.

Values are read from environment variables so secrets never live in the
source code. Copy .env.example to .env and fill in your own values for
local development. In production (e.g. Render) these are set as real
environment variables in the dashboard.
"""

import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Shared configuration for every environment."""

    # Flask uses this to sign session cookies and CSRF tokens. It MUST be
    # kept secret in production. We fall back to a random value so the app
    # still runs locally, but that fallback changes every restart, which
    # would silently log everyone out -- so we warn instead of hiding it.
    SECRET_KEY = os.environ.get("SECRET_KEY")

    DATABASE_PATH = os.environ.get(
        "DATABASE_PATH", os.path.join(BASE_DIR, "instance", "fintrack.db")
    )

    # Third-party API key for live currency conversion. The app degrades
    # gracefully (no conversion) if this isn't set.
    EXCHANGE_RATE_API_KEY = os.environ.get("EXCHANGE_RATE_API_KEY", "")
    EXCHANGE_RATE_BASE_URL = "https://v6.exchangerate-api.com/v6/"

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    WTF_CSRF_ENABLED = True


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


def get_config():
    env = os.environ.get("FLASK_ENV", "development").lower()
    return ProductionConfig if env == "production" else DevelopmentConfig
