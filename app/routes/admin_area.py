from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.auth.decorators import role_required, current_user
from app.services.anuncio_service import AnuncioService
from app.services.user_service import UserService
from app.services.area_service import AreaService
from app.services.tramite_service import TramiteService
from app.services.ventanilla_service import VentanillaService
from app.services.asignacion_service import AsignacionService
from app.services.suplente_service import SuplenteService

admin_area_bp = Blueprint("admin_area", __name__, url_prefix="/admin_area")

@admin_area_bp.route("/")
@login_required
@role_required("admin_area")
def dashboard():
    return render_template("admin_area/dashboard.html")


@admin_area_bp.route("/users")
@login_required
@role_required("admin_area")
def users():
    users = UserService.get_usuarios_by_area(current_user.area_id)
    return render_template("admin_area/users.html", users=users)


@admin_area_bp.route("/users/create", methods=["GET", "POST"])
@login_required
@role_required("admin_area")
def create_user():
    if request.method == "POST":
        user, error = UserService.create_user(
            username=request.form["username"],
            role="ventanilla",
            password=request.form["password"],
            nombre=request.form["nombre"],
            ap_paterno=request.form["ap_paterno"],
            ap_materno=request.form.get("ap_materno"),
            area_id= current_user.area_id
        )
        
        if error:
            flash(error, "error")
        else:
            flash("Usuario creado exitosamente", "success")
            return redirect(url_for("admin_area.users"))
            
    return render_template(
        "admin_area/form_user.html",
        user=None
    )


@admin_area_bp.route("/users/<int:id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin_area")
def edit_user(id):
    user = UserService.get_user_by_id(id)

    if request.method == "POST":
        user_updated, error = UserService.update_user(
            user_id=id,
            username=request.form["username"],
            role="ventanilla",
            password=request.form.get("password"),
            nombre=request.form["nombre"],
            ap_paterno=request.form["ap_paterno"],
            ap_materno=request.form.get("ap_materno"),
            area_id=current_user.area_id
        )
        
        if error:
            flash(error, "error")
        else:
            flash("Usuario actualizado exitosamente", "success")
            return redirect(url_for("admin_area.users"))

    return render_template(
        "admin_area/form_user.html",
        user=user
    )


@admin_area_bp.route("/users/<int:id>/delete", methods=["POST"])
@login_required
@role_required("admin_area")
def delete_user(id):
    success, error = UserService.delete_user(id)
    
    if error:
        flash(error, "error")
    else:
        flash("Usuario eliminado exitosamente", "success")
    
    return redirect(url_for("admin_area.users"))


@admin_area_bp.route('/users/<int:id_usuario>/tramites')
@login_required
@role_required("admin_area")
def tramites_usuario(id_usuario):
    usuario = UserService.get_user_by_id(id_usuario)

    asignaciones = AsignacionService.get_asignaciones_by_usuario(id_usuario)

    tramites_asignados_ids = {
        a.id_tramite for a in asignaciones
    }

    tramites_asignados = [
        TramiteService.get_tramite_by_id(tid)
        for tid in tramites_asignados_ids
    ]

    tramites_area = TramiteService.get_tramites_by_area(current_user.area_id)

    tramites_disponibles = [
        t for t in tramites_area
        if t.id_tramite not in tramites_asignados_ids
    ]

    return render_template(
        'admin_area/user_tramites.html',
        usuario=usuario,
        tramites_asignados=tramites_asignados,
        tramites=tramites_disponibles,
    )


@admin_area_bp.route('/tramites/asignar-usuario/<int:id_tramite>/<int:id_usuario>', methods=['POST'])
@login_required
@role_required("admin_area")
def asignar_usuario_tramite_post(id_tramite, id_usuario):
    tramite = TramiteService.get_tramite_by_id(id_tramite)
    usuario = UserService.get_user_by_id(id_usuario)

    redirect_to = request.form.get('next')

    if not tramite or not usuario:
        flash('Trámite o usuario no encontrado', 'danger')
        return redirect(redirect_to or url_for('admin_area.dashboard'))

    usuarios_ids_asignados = AsignacionService.get_usuarios_by_tramite(id_tramite)

    if id_usuario in usuarios_ids_asignados:
        flash('El usuario ya está asignado a este trámite', 'warning')
        return redirect(redirect_to)

    _, error = AsignacionService.create_asignacion(id_tramite, id_usuario)

    if error:
        flash(error, 'danger')
    else:
        flash('Usuario asignado correctamente al trámite', 'success')

    return redirect(redirect_to)


@admin_area_bp.route('/tramites/desasignar-usuario/<int:id_tramite>/<int:id_usuario>', methods=['POST'])
@login_required
@role_required("admin_area")
def desasignar_usuario_tramite(id_tramite, id_usuario):
    redirect_to = request.form.get('next')

    asignaciones = AsignacionService.get_asignaciones_by_tramite(id_tramite)

    asignacion = next(
        (a for a in asignaciones if a.id_usuario == id_usuario),
        None
    )

    if not asignacion:
        flash('El usuario no está asignado a este trámite', 'warning')
        return redirect(redirect_to)

    if error := AsignacionService.delete_asignacion(asignacion.id_asignacion):
        flash(error, 'danger')
    else:
        flash('Usuario desasignado correctamente del trámite', 'success')

    return redirect(redirect_to)


@admin_area_bp.route('/users/<int:id_usuario>/suplentes')
@login_required
@role_required("admin_area")
def suplentes_usuario(id_usuario):
    usuario = UserService.get_user_by_id(id_usuario)

    suplentes = SuplenteService.get_suplentes_by_usuario(id_usuario)

    suplentes_ids = [
        s.id_suplente_usuario for s in suplentes
    ]

    usuarios_no_asignados = SuplenteService.get_usuarios_disponibles_por_area(
        area_id=current_user.area_id,
        id_usuario=id_usuario,
        excluir_ids=suplentes_ids
    )

    return render_template(
        'admin_area/suplentes.html',
        usuario=usuario,
        suplentes=suplentes,
        usuarios_no_asignados=usuarios_no_asignados
    )


@admin_area_bp.route('/users/<int:id_usuario>/suplentes/asignar/<int:id_suplente_usuario>', methods=['POST'])
@login_required
@role_required("admin_area")
def asignar_suplente(id_usuario, id_suplente_usuario):
    _, error = SuplenteService.create_suplente(
        id_usuario=id_usuario,
        id_suplente_usuario=id_suplente_usuario
    )

    if error:
        flash(error, 'danger')
    else:
        flash('Suplente asignado correctamente', 'success')

    return redirect(url_for('admin_area.suplentes_usuario', id_usuario=id_usuario))


@admin_area_bp.route('/suplentes/<int:id_suplente>/eliminar', methods=['POST'])
@login_required
@role_required("admin_area")
def eliminar_suplente(id_suplente):
    suplente = SuplenteService.get_suplente_by_id(id_suplente)

    if error := SuplenteService.delete_suplente(id_suplente):
        flash(error, 'danger')
    else:
        flash('Suplente desasignado', 'success')

    return redirect(url_for('admin_area.suplentes_usuario', id_usuario=suplente.id_usuario))