let ticketId = null;
let ticketTurno = null;
let usuarioId = null;
let usuarioNombre = null;

function seleccionarTicket(e) {
    const card = e.currentTarget;

    if (card.classList.contains('selected')) {
        card.classList.remove('selected');
        ticketId = null;
        ticketTurno = null;
        validarAsignacion();
        return;
    }

    document.querySelectorAll('.ticket-card')
        .forEach(c => c.classList.remove('selected'));

    card.classList.add('selected');
    ticketId = card.dataset.ticketId;
    ticketTurno = card.dataset.turno;

    validarAsignacion();
}

function seleccionarUsuario(el) {
    if (el.classList.contains('disabled')) return;

    if (el.classList.contains('selected')) {
        el.classList.remove('selected');
        usuarioId = null;
        usuarioNombre = null;
        validarAsignacion();
        return;
    }

    document.querySelectorAll('.usuario-card')
        .forEach(u => u.classList.remove('selected'));

    el.classList.add('selected');
    usuarioId = el.dataset.usuarioId;
    usuarioNombre = el.dataset.nombre;

    validarAsignacion();
}

function validarAsignacion() {
    document.getElementById('btn-asignar').disabled = !(ticketId && usuarioId);
}

function abrirModal() {
    if (!ticketId || !usuarioId) return;

    document.getElementById('modal-ticket').textContent = ticketTurno;
    document.getElementById('modal-usuario').textContent = usuarioNombre;

    document.getElementById('input-ticket').value = ticketId;
    document.getElementById('input-usuario').value = usuarioId;

    document.getElementById('modal-confirmar').classList.add('active');
    document.getElementById('modal-overlay').classList.add('active');
}

function cerrarModal() {
    document.getElementById('modal-confirmar').classList.remove('active');
    document.getElementById('modal-overlay').classList.remove('active');
}