"""
Shared route decorators.

Every protected route in the original app.py repeated the same three
lines:

    if 'user_id' not in session:
        return redirect(url_for('login'))

That's a textbook case for a decorator -- it removes the duplication and
makes each route's real logic easier to see.
"""

from functools import wraps

from flask import redirect, session, url_for, flash


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)

    return wrapped_view
