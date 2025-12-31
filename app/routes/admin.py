from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.auth.decorators import login_required, role_required
from app.services.user_service import UserService
from app.services.area_service import AreaService
from app.services.tramite_service import TramiteService
from app.services.ventanilla_service import VentanillaService
from app.services.asignacion_service import AsignacionService
from app.services.suplente_service import SuplenteService

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
        user, error = UserService.create_user(
            username=request.form["username"],
            role=request.form["role"],
            password=request.form["password"],
            nombre=request.form["nombre"],
            ap_paterno=request.form["ap_paterno"],
            ap_materno=request.form.get("ap_materno")
        )
        
        if error:
            flash(error, "error")
        else:
            flash("Usuario creado exitosamente", "success")
            return redirect(url_for("admin.users"))
            
    return render_template("admin/form_user.html", user=None)


@admin_bp.route("/users/<int:id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_user(id):
    user = UserService.get_user_by_id_or_404(id)

    if request.method == "POST":
        user_updated, error = UserService.update_user(
            user_id=id,
            username=request.form["username"],
            role=request.form["role"],
            password=request.form.get("password"),
            nombre=request.form["nombre"],
            ap_paterno=request.form["ap_paterno"],
            ap_materno=request.form.get("ap_materno")
        )
        
        if error:
            flash(error, "error")
        else:
            flash("Usuario actualizado exitosamente", "success")
            return redirect(url_for("admin.users"))

    return render_template("admin/form_user.html", user=user)


@admin_bp.route("/users/<int:id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_user(id):
    success, error = UserService.delete_user(id)
    
    if error:
        flash(error, "error")
    else:
        flash("Usuario eliminado exitosamente", "success")
    
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
        
        area, error = AreaService.create_area(nombre)
        
        if error:
            flash(error, "error")
        else:
            flash("Área creada exitosamente", "success")
            return redirect(url_for("admin.areas"))
    
    return render_template("admin/form_area.html", area=None)


@admin_bp.route("/areas/<int:id_area>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_area(id_area):
    area = AreaService.get_area_by_id_or_404(id_area)
    
    if request.method == "POST":
        nombre = request.form.get("nombre", "")
        
        area_updated, error = AreaService.update_area(id_area, nombre)
        
        if error:
            flash(error, "error")
        else:
            flash("Área actualizada exitosamente", "success")
            return redirect(url_for("admin.areas"))
    
    return render_template("admin/form_area.html", area=area)


@admin_bp.route("/areas/<int:id_area>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_area(id_area):
    success, error = AreaService.delete_area(id_area)
    
    if error:
        flash(error, "error")
    else:
        flash("Área eliminada exitosamente", "success")
    
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
        
        tramite, error = TramiteService.create_tramite(id_area, nombre)
        
        if error:
            flash(error, "error")
        else:
            flash("Trámite creado exitosamente", "success")
            return redirect(url_for("admin.tramites", id_area=id_area))
    
    return render_template("admin/form_tramite.html", area=area, tramite=None)


@admin_bp.route("/tramites/<int:id_tramite>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_tramite(id_tramite):
    tramite = TramiteService.get_tramite_by_id_or_404(id_tramite)
    area = tramite.area
    
    if request.method == "POST":
        nombre = request.form.get("nombre", "")
        
        tramite_updated, error = TramiteService.update_tramite(id_tramite, nombre)
        
        if error:
            flash(error, "error")
        else:
            flash("Trámite actualizado exitosamente", "success")
            return redirect(url_for("admin.tramites", id_area=tramite.id_area))
    
    return render_template("admin/form_tramite.html", area=area, tramite=tramite)


@admin_bp.route("/tramites/<int:id_tramite>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_tramite(id_tramite):
    id_area, error = TramiteService.delete_tramite(id_tramite)
    
    if error:
        flash(error, "error")
        return redirect(url_for("admin.areas"))
    else:
        flash("Trámite eliminado exitosamente", "success")
        return redirect(url_for("admin.tramites", id_area=id_area))


@admin_bp.route('/ventanillas')
@login_required
@role_required("admin")
def ventanillas():
    ventanillas = VentanillaService.get_all_ventanillas()
    return render_template('admin/ventanillas.html', ventanillas=ventanillas)


@admin_bp.route('/ventanillas/create', methods=['GET', 'POST'])
@login_required
@role_required("admin")
def create_ventanilla():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        id_area = request.form.get('id_area', '').strip()
        id_area = int(id_area) if id_area else None
        
        ventanilla, error = VentanillaService.create_ventanilla(name, id_area)
        
        if error:
            flash(error, 'error')
        else:
            flash('Ventanilla creada exitosamente', 'success')
            return redirect(url_for('admin.ventanillas'))
    
    areas = AreaService.get_all_areas()
    return render_template('admin/form_ventanilla.html', areas=areas)


@admin_bp.route('/ventanillas/<int:id_ventanilla>/edit', methods=['GET', 'POST'])
@login_required
@role_required("admin")
def edit_ventanilla(id_ventanilla):
    ventanilla = VentanillaService.get_ventanilla_by_id(id_ventanilla)
    
    if not ventanilla:
        flash('Ventanilla no encontrada', 'error')
        return redirect(url_for('admin.ventanillas'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        id_area = request.form.get('id_area', '').strip()
        id_area = int(id_area) if id_area else None
        
        ventanilla_updated, error = VentanillaService.update_ventanilla(
            id_ventanilla, name, id_area
        )
        
        if error:
            flash(error, 'error')
        else:
            flash('Ventanilla actualizada exitosamente', 'success')
            return redirect(url_for('admin.ventanillas'))
    
    areas = AreaService.get_all_areas()
    return render_template('admin/form_ventanilla.html', 
                         ventanilla=ventanilla, areas=areas)


@admin_bp.route('/ventanillas/<int:id_ventanilla>/delete', methods=['POST'])
@login_required
@role_required("admin")
def delete_ventanilla(id_ventanilla):
    success, error = VentanillaService.delete_ventanilla(id_ventanilla)
    
    if error:
        flash(error, 'error')
    else:
        flash('Ventanilla eliminada exitosamente', 'success')
    
    return redirect(url_for('admin.ventanillas'))


@admin_bp.route('/ventanillas/asignar-usuario/<int:id_ventanilla>', methods=['GET'])
@login_required
def asignar_usuario_ventanilla(id_ventanilla):
    ventanilla = VentanillaService.get_ventanilla_by_id(id_ventanilla)
    
    if not ventanilla:
        flash('Ventanilla no encontrada', 'danger')
        return redirect(url_for('admin.ventanillas'))
    
    todos_usuarios = UserService.get_usuarios_by_role('ventanilla')
    
    usuarios_sin_ventanilla = []
    usuarios_con_ventanilla = []
    
    for usuario in todos_usuarios:
        if ventanilla.id_usuario and usuario.id_usuario == ventanilla.id_usuario:
            continue
            
        ventanilla_usuario = VentanillaService.get_ventanilla_by_usuario(usuario.id_usuario)
        
        if ventanilla_usuario:
            usuarios_con_ventanilla.append(usuario)
        else:
            usuarios_sin_ventanilla.append(usuario)
    
    return render_template(
        'admin/asignar_usuario_ventanilla.html',
        ventanilla=ventanilla,
        usuarios_sin_ventanilla=usuarios_sin_ventanilla,
        usuarios_con_ventanilla=usuarios_con_ventanilla
    )


@admin_bp.route('/ventanillas/asignar-usuario/<int:id_ventanilla>/<int:id_usuario>', methods=['POST'])
@login_required
def asignar_usuario_ventanilla_post(id_ventanilla, id_usuario):
    ventanilla = VentanillaService.get_ventanilla_by_id(id_ventanilla)
    
    if not ventanilla:
        flash('Ventanilla no encontrada', 'danger')
        return redirect(url_for('admin.ventanillas'))
    
    ventanilla_anterior = VentanillaService.get_ventanilla_by_usuario(id_usuario)
    
    if ventanilla_anterior:
        _, error = VentanillaService.desasignar_usuario(ventanilla_anterior.id_ventanilla)
        if error:
            flash(f'Error al desasignar de ventanilla anterior: {error}', 'danger')
            return redirect(url_for('admin.asignar_usuario_ventanilla', id_ventanilla=id_ventanilla))
    
    _, error = VentanillaService.asignar_usuario(id_ventanilla, id_usuario)
    
    if error:
        flash(f'Error al asignar usuario: {error}', 'danger')
    else:
        if ventanilla_anterior:
            flash(f'Usuario reasignado correctamente de "{ventanilla_anterior.name}" a "{ventanilla.name}"', 'success')
        else:
            flash('Usuario asignado correctamente', 'success')
    
    return redirect(url_for('admin.asignar_usuario_ventanilla', id_ventanilla=id_ventanilla))


@admin_bp.route('/ventanillas/desasignar-usuario/<int:id_ventanilla>', methods=['POST'])
@login_required
def desasignar_usuario_ventanilla(id_ventanilla):
    ventanilla = VentanillaService.get_ventanilla_by_id(id_ventanilla)
    
    if not ventanilla:
        flash('Ventanilla no encontrada', 'danger')
        return redirect(url_for('admin.ventanillas'))
    
    if not ventanilla.id_usuario:
        flash('Esta ventanilla no tiene usuario asignado', 'warning')
        return redirect(url_for('admin.asignar_usuario_ventanilla', id_ventanilla=id_ventanilla))
    
    _, error = VentanillaService.desasignar_usuario(id_ventanilla)
    
    if error:
        flash(f'Error al desasignar usuario: {error}', 'danger')
    else:
        flash('Usuario desasignado correctamente', 'success')
    
    return redirect(url_for('admin.asignar_usuario_ventanilla', id_ventanilla=id_ventanilla))


@admin_bp.route('/tramites/asignar-usuario/<int:id_tramite>', methods=['GET'])
@login_required
def asignar_usuario_tramite(id_tramite):
    tramite = TramiteService.get_tramite_by_id_or_404(id_tramite)

    todos_usuarios = UserService.get_usuarios_by_role('ventanilla')

    usuarios_ids_asignados = AsignacionService.get_usuarios_by_tramite(id_tramite)

    usuarios_asignados = [u for u in todos_usuarios if u.id_usuario in usuarios_ids_asignados]
    usuarios_sin_asignar = [u for u in todos_usuarios if u.id_usuario not in usuarios_ids_asignados]

    return render_template(
        'admin/asignar_usuario_tramite.html',
        tramite=tramite,
        usuarios_asignados=usuarios_asignados,
        usuarios_sin_asignar=usuarios_sin_asignar
    )


@admin_bp.route('/tramites/asignar-usuario/<int:id_tramite>/<int:id_usuario>', methods=['POST'])
@login_required
def asignar_usuario_tramite_post(id_tramite, id_usuario):
    tramite = TramiteService.get_tramite_by_id(id_tramite)
    usuario = UserService.get_user_by_id(id_usuario)

    redirect_to = request.form.get('next')

    if not tramite or not usuario:
        flash('Trámite o usuario no encontrado', 'danger')
        return redirect(redirect_to or url_for('admin.index'))

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

@admin_bp.route('/tramites/desasignar-usuario/<int:id_tramite>/<int:id_usuario>', methods=['POST'])
@login_required
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

    error = AsignacionService.delete_asignacion(asignacion.id_asignacion)

    if error:
        flash(error, 'danger')
    else:
        flash('Usuario desasignado correctamente del trámite', 'success')

    return redirect(redirect_to)


@admin_bp.route('/users/<int:id_usuario>/tramites')
def tramites_usuario(id_usuario):
    usuario = UserService.get_user_by_id_or_404(id_usuario)

    asignaciones = AsignacionService.get_asignaciones_by_usuario(id_usuario)

    tramites_asignados_ids = {
        asignacion.id_tramite for asignacion in asignaciones
    }

    tramites_asignados = [
        TramiteService.get_tramite_by_id(tramite_id)
        for tramite_id in tramites_asignados_ids
    ]

    areas = AreaService.get_all_areas()
    tramites_por_area = {}

    for area in areas:
        tramites_area = TramiteService.get_tramites_by_area(area.id_area)

        tramites_no_asignados = [
            tramite for tramite in tramites_area
            if tramite.id_tramite not in tramites_asignados_ids
        ]

        if tramites_no_asignados:
            tramites_por_area[area] = tramites_no_asignados

    return render_template(
        'admin/user_tramites.html',
        usuario=usuario,
        tramites_asignados=tramites_asignados,
        tramites_por_area=tramites_por_area
    )


@admin_bp.route('/users/<int:id_usuario>/suplentes')
@login_required
def suplentes_usuario(id_usuario):
    usuario = UserService.get_user_by_id_or_404(id_usuario)

    suplentes = SuplenteService.get_suplentes_by_usuario(id_usuario)

    suplentes_activos = [s for s in suplentes if s.activo]
    suplentes_inactivos = [s for s in suplentes if not s.activo]

    suplentes_ids = {s.id_suplente_usuario for s in suplentes}

    todos_usuarios = UserService.get_usuarios_by_role('ventanilla')
    usuarios_no_asignados = [
        u for u in todos_usuarios
        if u.id_usuario != id_usuario and u.id_usuario not in suplentes_ids
    ]

    return render_template(
        'admin/suplentes.html',
        usuario=usuario,
        suplentes_activos=suplentes_activos,
        suplentes_inactivos=suplentes_inactivos,
        usuarios_no_asignados=usuarios_no_asignados
    )


@admin_bp.route('/users/<int:id_usuario>/suplentes/asignar/<int:id_suplente_usuario>', methods=['POST'])
@login_required
def asignar_suplente(id_usuario, id_suplente_usuario):
    _, error = SuplenteService.create_suplente(
        id_usuario=id_usuario,
        id_suplente_usuario=id_suplente_usuario,
        activo=False
    )

    if error:
        flash(error, 'danger')
    else:
        flash('Suplente asignado correctamente', 'success')

    return redirect(url_for('admin.suplentes_usuario', id_usuario=id_usuario))


@admin_bp.route('/suplentes/<int:id_suplente>/activar', methods=['POST'])
@login_required
def activar_suplente(id_suplente):
    ok, error = SuplenteService.activate_suplente(id_suplente)

    if error:
        flash(error, 'danger')
    else:
        flash('Suplente activado', 'success')

    suplente = SuplenteService.get_suplente_by_id(id_suplente)
    return redirect(url_for('admin.suplentes_usuario', id_usuario=suplente.id_usuario))


@admin_bp.route('/suplentes/<int:id_suplente>/desactivar', methods=['POST'])
@login_required
def desactivar_suplente(id_suplente):
    ok, error = SuplenteService.deactivate_suplente(id_suplente)

    if error:
        flash(error, 'danger')
    else:
        flash('Suplente desactivado', 'success')

    suplente = SuplenteService.get_suplente_by_id(id_suplente)
    return redirect(url_for('admin.suplentes_usuario', id_usuario=suplente.id_usuario))


@admin_bp.route('/suplentes/<int:id_suplente>/eliminar', methods=['POST'])
@login_required
def eliminar_suplente(id_suplente):
    suplente = SuplenteService.get_suplente_by_id(id_suplente)

    error = SuplenteService.delete_suplente(id_suplente)

    if error:
        flash(error, 'danger')
    else:
        flash('Suplente desasignado', 'success')

    return redirect(url_for('admin.suplentes_usuario', id_usuario=suplente.id_usuario))
