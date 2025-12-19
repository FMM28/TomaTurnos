from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Usuario
from app.extensions import db
from app.auth.decorators import login_required, role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/")
@login_required
@role_required("admin")
def dashboard():
    return render_template("admin/dashboard.html")

@admin_bp.route("/users")
@login_required
@role_required("admin")
def users():
    users = Usuario.query.all()
    return render_template("admin/users.html", users=users)

@admin_bp.route("/users/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def create_user():
    if request.method == "POST":
        user = Usuario(
            username=request.form["username"],
            role=request.form["role"]
        )
        user.set_password(request.form["password"])

        db.session.add(user)
        db.session.commit()

        flash("Usuario creado correctamente", "success")
        return redirect(url_for("admin.users"))
    return render_template("admin/create_user.html")

@admin_bp.route("/users/<int:id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_user(id):
    user = Usuario.query.get_or_404(id)

    if request.method == "POST":
        user.username = request.form["username"]
        user.role = request.form["role"]

        if request.form.get("password"):
            user.set_password(request.form["password"])

        db.session.commit()
        flash("Usuario actualizado", "success")
        return redirect(url_for("admin.users"))

    return render_template("admin/edit_user.html", user=user)

@admin_bp.route("/users/<int:id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_user(id):
    user = Usuario.query.get_or_404(id)

    db.session.delete(user)
    db.session.commit()

    flash("Usuario eliminado", "info")
    return redirect(url_for("admin.users"))
