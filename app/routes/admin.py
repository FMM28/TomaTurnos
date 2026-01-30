from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.auth.decorators import role_required
from app.services.anuncio_service import AnuncioService
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
            ap_materno=request.form.get("ap_materno"),
            area_id=request.form.get("area", type=int)
        )
        
        if error:
            flash(error, "error")
        else:
            flash("Usuario creado exitosamente", "success")
            return redirect(url_for("admin.users"))
            
    return render_template(
        "admin/form_user.html",
        user=None,
        areas=AreaService.get_all_areas()
    )


@admin_bp.route("/users/<int:id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_user(id):
    user = UserService.get_user_by_id(id)

    if request.method == "POST":
        user_updated, error = UserService.update_user(
            user_id=id,
            username=request.form["username"],
            role=request.form["role"],
            password=request.form.get("password"),
            nombre=request.form["nombre"],
            ap_paterno=request.form["ap_paterno"],
            ap_materno=request.form.get("ap_materno"),
            area_id=request.form.get("area", type=int)
        )
        
        if error:
            flash(error, "error")
        else:
            flash("Usuario actualizado exitosamente", "success")
            return redirect(url_for("admin.users"))

    return render_template(
        "admin/form_user.html",
        user=user,
        areas=AreaService.get_all_areas()
    )


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
    area = AreaService.get_area_by_id(id_area)
    
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
    area = AreaService.get_area_by_id(id_area)
    tramites = TramiteService.get_tramites_by_area(id_area)
    return render_template("admin/tramites.html", area=area, tramites=tramites)


@admin_bp.route("/areas/<int:id_area>/tramites/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def create_tramite(id_area):
    area = AreaService.get_area_by_id(id_area)
    
    if request.method == "POST":
        nombre = request.form.get("nombre", "")
        requerimientos = request.form.get("requerimientos", None)
        
        tramite, error = TramiteService.create_tramite(id_area, nombre, requerimientos)
        
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
    tramite = TramiteService.get_tramite_by_id(id_tramite)
    area = tramite.area
    
    if request.method == "POST":
        nombre = request.form.get("nombre", "")
        requerimientos = request.form.get("requerimientos", None)
        
        tramite_updated, error = TramiteService.update_tramite(id_tramite, nombre, requerimientos)
        
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


@admin_bp.route('/ventanillas/<int:id_ventanilla>/tramites')
@login_required
@role_required("admin")
def ventanilla_tramites(id_ventanilla):
    ventanilla = VentanillaService.get_ventanilla_by_id(id_ventanilla)
    if not ventanilla:
        flash('Ventanilla no encontrada', 'danger')
        return redirect(url_for('admin.ventanillas'))

    tramites_ventanilla = TramiteService.get_tramites_by_ventanilla(
        id_ventanilla
    )

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
        'admin/asignar_tramite_ventanilla.html',
        ventanilla=ventanilla,
        tramites_ventanilla=tramites_ventanilla,
        tramites_sin_ventanilla=tramites_sin_ventanilla,
        tramites_con_otra_ventanilla=tramites_con_otra_ventanilla
    )


@admin_bp.route('/ventanillas/<int:id_ventanilla>/tramites/<int:id_tramite>', methods=['POST'])
@login_required
@role_required("admin")
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


@admin_bp.route('/ventanillas/<int:id_ventanilla>/tramites/<int:id_tramite>/delete', methods=['POST'])
@login_required
@role_required("admin")
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


@admin_bp.route('/tramites/asignar-usuario/<int:id_tramite>', methods=['GET'])
@login_required
def asignar_usuario_tramite(id_tramite):
    tramite = TramiteService.get_tramite_by_id(id_tramite)

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

    if error := AsignacionService.delete_asignacion(asignacion.id_asignacion):
        flash(error, 'danger')
    else:
        flash('Usuario desasignado correctamente del trámite', 'success')

    return redirect(redirect_to)


@admin_bp.route('/tramites/<int:id_tramite>/ventanilla')
@login_required
@role_required("admin")
def tramite_ventanilla(id_tramite):
    tramite = TramiteService.get_tramite_by_id(id_tramite)
    if not tramite:
        flash('Trámite no encontrado', 'danger')
        return redirect(url_for('admin.areas'))

    ventanillas = VentanillaService.get_ventanillas_by_area(tramite.id_area)

    return render_template('admin/form_tramite_ventanilla.html', tramite=tramite, ventanillas=ventanillas)


@admin_bp.route('/users/<int:id_usuario>/tramites')
def tramites_usuario(id_usuario):
    usuario = UserService.get_user_by_id(id_usuario)

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

        if tramites_no_asignados := [
            tramite for tramite in tramites_area
            if tramite.id_tramite not in tramites_asignados_ids
        ]:
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
    usuario = UserService.get_user_by_id(id_usuario)

    suplentes = SuplenteService.get_suplentes_by_usuario(id_usuario)

    suplentes_ids = [
        s.id_suplente_usuario for s in suplentes
    ]

    usuarios_no_asignados = SuplenteService.get_usuarios_disponibles(
        id_usuario=id_usuario,
        excluir_ids=suplentes_ids
    )

    return render_template(
        'admin/suplentes.html',
        usuario=usuario,
        suplentes=suplentes,
        usuarios_no_asignados=usuarios_no_asignados
    )


@admin_bp.route('/users/<int:id_usuario>/suplentes/asignar/<int:id_suplente_usuario>', methods=['POST'])
@login_required
def asignar_suplente(id_usuario, id_suplente_usuario):
    _, error = SuplenteService.create_suplente(
        id_usuario=id_usuario,
        id_suplente_usuario=id_suplente_usuario
    )

    if error:
        flash(error, 'danger')
    else:
        flash('Suplente asignado correctamente', 'success')

    return redirect(url_for('admin.suplentes_usuario', id_usuario=id_usuario))


@admin_bp.route('/suplentes/<int:id_suplente>/eliminar', methods=['POST'])
@login_required
def eliminar_suplente(id_suplente):
    suplente = SuplenteService.get_suplente_by_id(id_suplente)

    if error := SuplenteService.delete_suplente(id_suplente):
        flash(error, 'danger')
    else:
        flash('Suplente desasignado', 'success')

    return redirect(url_for('admin.suplentes_usuario', id_usuario=suplente.id_usuario))


@admin_bp.route("/anuncios")
@login_required
@role_required("admin")
def anuncios():
    return render_template(
        "admin/anuncios.html",
        anuncios=AnuncioService.get_all()
    )


@admin_bp.route("/anuncios/nuevo", methods=["GET", "POST"])
@login_required
@role_required("admin")
def create_anuncio():
    if request.method == "POST":

        anuncio, error = AnuncioService.create(
            archivo=request.files.get("archivo"),
            titulo=request.form.get("titulo"),
            tipo=request.form.get("tipo"),
            duracion=request.form.get("duracion", type=int)
        )

        if error:
            flash(error, "error")
            return redirect(request.url)

        flash("Anuncio creado correctamente", "success")
        return redirect(url_for("admin.anuncios"))

    return render_template("admin/form_anuncio.html", anuncio=None)


@admin_bp.route("/anuncios/<int:id_anuncio>/editar", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_anuncio(id_anuncio):
    anuncio = AnuncioService.get_by_id(id_anuncio)
    if not anuncio:
        flash("Anuncio no encontrado", "error")
        return redirect(url_for("admin.anuncios"))

    if request.method == "POST":
        anuncio, error = AnuncioService.update(
            id_anuncio=id_anuncio,
            archivo=request.files.get("archivo"),
            duracion=request.form.get("duracion", type=int),
            activo=bool(request.form.get("activo"))
        )

        if error:
            flash(error, "error")
            return redirect(request.url)

        flash("Anuncio actualizado correctamente", "success")
        return redirect(url_for("admin.anuncios"))

    return render_template("admin/form_anuncio.html", anuncio=anuncio)


@admin_bp.route("/anuncios/<int:id_anuncio>/desactivar", methods=["POST"])
@login_required
@role_required("admin")
def deactivate_anuncio(id_anuncio):
    anuncio, error = AnuncioService.toggle_active(id_anuncio)
    if anuncio:
        flash("Anuncio desactivado correctamente", "success")
    else:
        flash(f"No se pudo desactivar el anuncio: {error}", "error")

    return redirect(url_for("admin.anuncios"))


@admin_bp.route("/anuncios/<int:id_anuncio>/activar", methods=["POST"])
@login_required
@role_required("admin")
def activate_anuncio(id_anuncio):
    anuncio, error = AnuncioService.toggle_active(id_anuncio)
    if anuncio:
        flash("Anuncio activado correctamente", "success")
    else:
        flash(f"No se pudo activar el anuncio: {error}", "error")

    return redirect(url_for("admin.anuncios"))


@admin_bp.route("/anuncios/<int:id_anuncio>/eliminar", methods=["POST"])
@login_required
@role_required("admin")
def delete_anuncio(id_anuncio):
    if AnuncioService.delete(id_anuncio):
        flash("Anuncio eliminado", "success")
    else:
        flash("No se pudo eliminar el anuncio", "error")

    return redirect(url_for("admin.anuncios"))
