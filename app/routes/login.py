from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import Usuario

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = Usuario.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session["user_id"] = user.id_usuario
            session["username"] = user.username
            session["role"] = user.role
            
            if user.role == "admin":
                return redirect(url_for("admin.dashboard"))
            elif user.role == "ventanilla":
                return redirect(url_for("ventanilla.dashboard"))
            elif user.role == "kiosco":
                return redirect(url_for("kiosco.dashboard"))

        flash("Usuario o contraseña incorrectos", "danger")

    return render_template("login/login.html")



@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada", "info")
    return redirect(url_for("auth.login"))