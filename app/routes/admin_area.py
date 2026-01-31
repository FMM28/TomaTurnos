from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.auth.decorators import role_required, current_user
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


@admin_area_bp.route("/tramites")
@login_required
@role_required("admin_area")
def tramites():
    tramites = TramiteService.get_tramites_by_area(current_user.area_id)
    return render_template("admin_area/tramites.html", tramites=tramites)


@admin_area_bp.route("/tramites/create", methods=["GET", "POST"])
@login_required
@role_required("admin_area")
def create_tramite():
    area = AreaService.get_area_by_id(current_user.area_id)
    
    if request.method == "POST":
        nombre = request.form.get("nombre", "")
        requerimientos = request.form.get("requerimientos", None)
        
        tramite, error = TramiteService.create_tramite(current_user.area_id, nombre, requerimientos)
        
        if error:
            flash(error, "error")
        else:
            flash("Trámite creado exitosamente", "success")
            return redirect(url_for("admin_area.tramites"))
    
    return render_template("admin_area/form_tramite.html", tramite=None)


@admin_area_bp.route("/tramites/<int:id_tramite>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin_area")
def edit_tramite(id_tramite):
    tramite = TramiteService.get_tramite_by_id(id_tramite)

    
    if request.method == "POST":
        nombre = request.form.get("nombre", "")
        requerimientos = request.form.get("requerimientos", None)
        
        tramite_updated, error = TramiteService.update_tramite(id_tramite, nombre, requerimientos)
        
        if error:
            flash(error, "error")
        else:
            flash("Trámite actualizado exitosamente", "success")
            return redirect(url_for("admin_area.tramites"))
    
    return render_template("admin_area/form_tramite.html", tramite=tramite)


@admin_area_bp.route("/tramites/<int:id_tramite>/delete", methods=["POST"])
@login_required
@role_required("admin_area")
def delete_tramite(id_tramite):
    success, error = TramiteService.delete_tramite(id_tramite)
    
    if error:
        flash(error, "error")
    else:
        flash("Trámite eliminado exitosamente", "success")
    
    return redirect(url_for("admin_area.tramites"))


@admin_area_bp.route('/ventanillas')
@login_required
@role_required("admin_area")
def ventanillas():
    ventanillas = VentanillaService.get_ventanillas_by_area(current_user.area_id)
    return render_template('admin_area/ventanillas.html', ventanillas=ventanillas)


@admin_area_bp.route('/ventanillas/create', methods=['GET', 'POST'])
@login_required
@role_required("admin_area")
def create_ventanilla():
    if request.method == 'POST':
        name = request.form.get('name', '')
        
        ventanilla, error = VentanillaService.create_ventanilla(name, current_user.area_id)
        
        if error:
            flash(error, 'error')
        else:
            flash('Ventanilla creada exitosamente', 'success')
            return redirect(url_for('admin_area.ventanillas'))
    
    return render_template('admin_area/form_ventanilla.html',ventanilla=None)


@admin_area_bp.route('/ventanillas/<int:id_ventanilla>/edit', methods=['GET', 'POST'])
@login_required
@role_required("admin_area")
def edit_ventanilla(id_ventanilla):
    ventanilla = VentanillaService.get_ventanilla_by_id(id_ventanilla)
    
    if not ventanilla:
        flash('Ventanilla no encontrada', 'error')
        return redirect(url_for('admin_area.ventanillas'))
    
    if request.method == 'POST':
        name = request.form.get('name', '')
        ventanilla_updated, error = VentanillaService.update_ventanilla(id_ventanilla, name, current_user.area_id)
        
        if error:
            flash(error, 'error')
        else:
            flash('Ventanilla actualizada exitosamente', 'success')
            return redirect(url_for('admin_area.ventanillas'))
    
    areas = AreaService.get_all_areas()
    return render_template('admin_area/form_ventanilla.html', ventanilla=ventanilla)


@admin_area_bp.route('/ventanillas/<int:id_ventanilla>/delete', methods=['POST'])
@login_required
@role_required("admin_area")
def delete_ventanilla(id_ventanilla):
    success, error = VentanillaService.delete_ventanilla(id_ventanilla)
    
    if error:
        flash(error, 'error')
    else:
        flash('Ventanilla eliminada exitosamente', 'success')
    
    return redirect(url_for('admin_area.ventanillas'))


@admin_area_bp.route('/ventanillas/<int:id_ventanilla>/tramites')
@login_required
@role_required("admin_area")
def ventanilla_tramites(id_ventanilla):
    ventanilla = VentanillaService.get_ventanilla_by_id(id_ventanilla)
    if not ventanilla:
        flash('Ventanilla no encontrada', 'danger')
        return redirect(url_for('admin_area.ventanillas'))

    tramites_ventanilla = TramiteService.get_tramites_by_ventanilla(id_ventanilla)

    tramites_area = TramiteService.get_tramites_by_area_excluyendo(
        ventanilla.id_area,
        {t.id_tramite for t in tramites_ventanilla}
    )

    tramites_sin_ventanilla = []
    tramites_con_otra_ventanilla = []

    for tramite in tramites_area:
        if not tramite.id_ventanilla:
            tramites_sin_ventanilla.append(tramite)
        else:
            tramites_con_otra_ventanilla.append(tramite)

    return render_template(
        'admin_area/asignar_tramite_ventanilla.html',
        ventanilla=ventanilla,
        tramites_ventanilla=tramites_ventanilla,
        tramites_sin_ventanilla=tramites_sin_ventanilla,
        tramites_con_otra_ventanilla=tramites_con_otra_ventanilla
    )


@admin_area_bp.route('/tramites/<int:id_tramite>/ventanilla')
@login_required
@role_required("admin_area")
def tramite_ventanilla(id_tramite):
    tramite = TramiteService.get_tramite_by_id(id_tramite)
    if not tramite:
        flash('Trámite no encontrado', 'danger')
        return redirect(url_for('admin_area.areas'))

    ventanillas = VentanillaService.get_ventanillas_by_area(tramite.id_area)

    return render_template('admin_area/form_tramite_ventanilla.html', tramite=tramite, ventanillas=ventanillas)

@admin_area_bp.route('/ventanillas/<int:id_ventanilla>/tramites/<int:id_tramite>', methods=['POST'])
@login_required
@role_required("admin_area")
def asignar_tramite_ventanilla(id_ventanilla, id_tramite):
    redirect_to = request.form.get('next')

    ventanilla = VentanillaService.get_ventanilla_by_id(id_ventanilla)
    tramite = TramiteService.get_tramite_by_id(id_tramite)

    if not ventanilla or not tramite:
        flash('Ventanilla o trámite no encontrados', 'error')
        return redirect(redirect_to)

    _, error = TramiteService.asignar_tramite_a_ventanilla(
        id_tramite,
        id_ventanilla
    )

    if error:
        flash(error, 'danger')
    else:
        flash('Trámite asignado correctamente a la ventanilla', 'success')
    
    return redirect(redirect_to)


@admin_area_bp.route('/ventanillas/<int:id_ventanilla>/tramites/<int:id_tramite>/delete', methods=['POST'])
@login_required
@role_required("admin_area")
def desasignar_tramite_ventanilla(id_ventanilla, id_tramite):
    redirect_to = request.form.get('next')

    tramite = TramiteService.get_tramite_by_id(id_tramite)

    if not tramite:
        flash('Trámite no encontrado', 'error')
        return redirect(redirect_to)

    _, error = TramiteService.desasignar_tramite_de_ventanilla(
        id_tramite
    )

    if error:
        flash(error, 'danger')
    else:
        flash('Trámite desasignado correctamente de la ventanilla', 'success')

    return redirect(redirect_to)


@admin_area_bp.route('/tramites/asignar-usuario/<int:id_tramite>', methods=['GET'])
@login_required
@role_required("admin_area")
def asignar_usuario_tramite(id_tramite):
    tramite = TramiteService.get_tramite_by_id(id_tramite)

    todos_usuarios = UserService.get_usuarios_by_area(current_user.area_id)

    usuarios_ids_asignados = AsignacionService.get_usuarios_by_tramite(id_tramite)

    usuarios_asignados = [u for u in todos_usuarios if u.id_usuario in usuarios_ids_asignados]
    usuarios_sin_asignar = [u for u in todos_usuarios if u.id_usuario not in usuarios_ids_asignados]

    return render_template(
        'admin_area/asignar_usuario_tramite.html',
        tramite=tramite,
        usuarios_asignados=usuarios_asignados,
        usuarios_sin_asignar=usuarios_sin_asignar
    )