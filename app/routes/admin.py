from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.auth.decorators import login_required, role_required
from app.services.user_service import UserService
from app.services.area_service import AreaService
from app.services.tramite_service import TramiteService

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
    users = UserService.get_all_users()
    return render_template("admin/users.html", users=users)


@admin_bp.route("/users/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def create_user():
    if request.method == "POST":
        try:
            UserService.create_user(
                username=request.form["username"],
                role=request.form["role"],
                password=request.form["password"]
            )
            flash("Usuario creado correctamente", "success")
            return redirect(url_for("admin.users"))
        except Exception as e:
            flash(f"Error al crear usuario: {str(e)}", "error")
            
    return render_template("admin/create_user.html")


@admin_bp.route("/users/<int:id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_user(id):
    user = UserService.get_user_by_id_or_404(id)

    if request.method == "POST":
        try:
            UserService.update_user(
                user_id=id,
                username=request.form["username"],
                role=request.form["role"],
                password=request.form.get("password")
            )
            flash("Usuario actualizado correctamente", "success")
            return redirect(url_for("admin.users"))
        except Exception as e:
            flash(f"Error al actualizar usuario: {str(e)}", "error")

    return render_template("admin/edit_user.html", user=user)


@admin_bp.route("/users/<int:id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_user(id):
    try:
        UserService.delete_user(id)
        flash("Usuario eliminado correctamente", "info")
    except Exception as e:
        flash(f"Error al eliminar usuario: {str(e)}", "error")
    
    return redirect(url_for("admin.users"))


@admin_bp.route("/areas")
@login_required
@role_required("admin")
def areas():
    areas = AreaService.get_all_areas()
    return render_template("admin/areas.html", areas=areas)


@admin_bp.route("/areas/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def create_area():
    if request.method == "POST":
        nombre = request.form.get("nombre", "")
        
        try:
            AreaService.create_area(nombre)
            flash("Área creada exitosamente", "success")
            return redirect(url_for("admin.areas"))
        except ValueError as e:
            flash(str(e), "error")
        except Exception as e:
            flash(str(e), "error")
    
    return render_template("admin/form_area.html", area=None)


@admin_bp.route("/areas/<int:id_area>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_area(id_area):
    area = AreaService.get_area_by_id_or_404(id_area)
    
    if request.method == "POST":
        nombre = request.form.get("nombre", "")
        
        try:
            AreaService.update_area(id_area, nombre)
            flash("Área actualizada exitosamente", "success")
            return redirect(url_for("admin.areas"))
        except ValueError as e:
            flash(str(e), "error")
        except Exception as e:
            flash(str(e), "error")
    
    return render_template("admin/form_area.html", area=area)


@admin_bp.route("/areas/<int:id_area>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_area(id_area):
    try:
        AreaService.delete_area(id_area)
        flash("Área eliminada exitosamente", "success")
    except Exception as e:
        flash(str(e), "error")
    
    return redirect(url_for("admin.areas"))


@admin_bp.route("/areas/<int:id_area>/tramites")
@login_required
@role_required("admin")
def tramites(id_area):
    area = AreaService.get_area_by_id_or_404(id_area)
    tramites = TramiteService.get_tramites_by_area(id_area)
    return render_template("admin/tramites.html", area=area, tramites=tramites)


@admin_bp.route("/areas/<int:id_area>/tramites/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def create_tramite(id_area):
    area = AreaService.get_area_by_id_or_404(id_area)
    
    if request.method == "POST":
        nombre = request.form.get("nombre", "")
        
        try:
            TramiteService.create_tramite(id_area, nombre)
            flash("Trámite creado exitosamente", "success")
            return redirect(url_for("admin.tramites", id_area=id_area))
        except ValueError as e:
            flash(str(e), "error")
        except Exception as e:
            flash(str(e), "error")
    
    return render_template("admin/form_tramite.html", area=area, tramite=None)


@admin_bp.route("/tramites/<int:id_tramite>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_tramite(id_tramite):
    tramite = TramiteService.get_tramite_by_id_or_404(id_tramite)
    area = tramite.area
    
    if request.method == "POST":
        nombre = request.form.get("nombre", "")
        
        try:
            TramiteService.update_tramite(id_tramite, nombre)
            flash("Trámite actualizado exitosamente", "success")
            return redirect(url_for("admin.tramites", id_area=tramite.id_area))
        except ValueError as e:
            flash(str(e), "error")
        except Exception as e:
            flash(str(e), "error")
    
    return render_template("admin/form_tramite.html", area=area, tramite=tramite)


@admin_bp.route("/tramites/<int:id_tramite>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_tramite(id_tramite):
    try:
        id_area = TramiteService.delete_tramite(id_tramite)
        flash("Trámite eliminado exitosamente", "success")
        return redirect(url_for("admin.tramites", id_area=id_area))
    except Exception as e:
        flash(str(e), "error")
        return redirect(url_for("admin.areas"))