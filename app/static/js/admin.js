function confirmarReasignacion(idUsuario, nombreUsuario, ventanillaActual, ventanillaNueva) {
    const modal = document.getElementById('confirmModal');
    const message = document.getElementById('confirmMessage');
    const form = document.getElementById('reassignForm');
    
    message.textContent = `El usuario "${nombreUsuario}" está actualmente asignado a "${ventanillaActual}". ¿Desea reasignarlo a "${ventanillaNueva}"?`;
    
    form.action = "{{ url_for('admin.asignar_usuario_ventanilla_post', id_ventanilla=ventanilla.id_ventanilla, id_usuario=0) }}".replace('/0', '/' + idUsuario);
    
    modal.style.display = 'block';
}

function cerrarModal() {
    document.getElementById('confirmModal').style.display = 'none';
}

window.onclick = function(event) {
    const modal = document.getElementById('confirmModal');
    if (event.target == modal) {
        cerrarModal();
    }
}