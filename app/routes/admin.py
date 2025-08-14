import os
from flask import Blueprint, jsonify, session, redirect, url_for, request, render_template_string, render_template
from functools import wraps
from app.data.database import get_upcoming_fight_data, get_fighter_by_id

# Load from environment
ADMIN_USERNAME = os.getenv("ADMIN_USER")
ADMIN_PASSWORD = os.getenv("ADMIN_PASS")
SECRET_PATH = os.getenv("SECRET_ADMIN_PATH")

admin_bp = Blueprint("admin", __name__)

# Decorator for requiring login
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)
    return decorated

# Admin dashboard
@admin_bp.route(SECRET_PATH)
@admin_required
def dashboard():
    upcoming_fights = get_upcoming_fight_data()
    return render_template("admin.html", upcoming_fights=upcoming_fights)

# Login
@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form["username"] == ADMIN_USERNAME and request.form["password"] == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(SECRET_PATH)
        else:
            error = "Invalid credentials. Please try again."

    return render_template("admin-login.html", error=error)

# Logout
@admin_bp.route("/logout")
def logout():
    session.clear()
    return "Logged out."