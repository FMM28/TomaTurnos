from flask import Blueprint, jsonify, session, redirect, url_for
from flask_wtf.csrf import generate_csrf

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return "Login correcto"

@main_bp.route("/refresh-csrf", methods=["GET"])
def refresh_csrf():
    return jsonify({
        "csrf_token": generate_csrf()
    })