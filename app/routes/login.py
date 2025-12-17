from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import Usuario
from app.extensions import db, bcrypt

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = Usuario.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session["user_id"] = user.id_usuario
            session["role"] = user.role
            flash("Bienvenido", "success")
            return redirect(url_for("main.index"))

        flash("Usuario o contraseña incorrectos", "danger")

    return render_template("login/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada", "info")
    return redirect(url_for("auth.login"))