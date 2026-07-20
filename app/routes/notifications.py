"""In-app notifications (budget alerts, sharing alerts, etc.)."""

from flask import Blueprint, render_template, session, redirect, url_for, flash

from app.extensions import db
from app.utils.decorators import login_required

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/notifications")
@login_required
def notifications():
    user_id = session["user_id"]
    items = db.execute(
        "SELECT * FROM notifications WHERE user_id = ? ORDER BY timestamp DESC", user_id
    )
    return render_template("notifications.html", notifications=items)


@notifications_bp.route("/delete_notification/<int:notification_id>", methods=["POST"])
@login_required
def delete_notification(notification_id):
    user_id = session["user_id"]
    db.execute(
        "DELETE FROM notifications WHERE id = ? AND user_id = ?", notification_id, user_id
    )
    flash("Notification deleted successfully!", "success")
    return redirect(url_for("notifications.notifications"))
