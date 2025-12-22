from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.auth.decorators import login_required, role_required
from app.services.user_service import UserService
from app.services.area_service import AreaService
from app.services.tramite_service import TramiteService
from app.services.ventanilla_service import VentanillaService

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
            password=request.form["password"]
        )
        
        if error:
            flash(error, "error")
        else:
            flash("Usuario creado exitosamente", "success")
            return redirect(url_for("admin.users"))
            
    return render_template("admin/create_user.html")


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
            password=request.form.get("password")
        )
        
        if error:
            flash(error, "error")
        else:
            flash("Usuario actualizado exitosamente", "success")
            return redirect(url_for("admin.users"))

    return render_template("admin/edit_user.html", user=user)


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