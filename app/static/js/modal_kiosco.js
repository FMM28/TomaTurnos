let currentFormId = null;

function showModal(tramiteName, formId) {
    currentFormId = formId;
    document.getElementById('modalTramiteName').textContent = 
        `¿Está seguro que desea eliminar "${tramiteName}" de su selección?`;
    document.getElementById('confirmModal').classList.add('active');
}

function closeModal() {
    document.getElementById('confirmModal').classList.remove('active');
    currentFormId = null;
}

function confirmRemove() {
    if (currentFormId) {
        document.getElementById(currentFormId).submit();
    }
}

document.getElementById('confirmModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeModal();
    }
});

let tramiteFormActual = null;

function handleTramiteClick(button) {
    const requerimientos = button.dataset.requerimientos?.trim();
    tramiteFormActual = button.closest("form");

    if (!requerimientos) {
        tramiteFormActual.submit();
        return;
    }

    const list = document.getElementById("requerimientosList");
    list.innerHTML = "";

    requerimientos.split("\n").forEach(req => {
        if (req.trim()) {
            const li = document.createElement("li");
            li.textContent = req;
            list.appendChild(li);
        }
    });

    document.getElementById("requerimientosModal").classList.add("active");
}

function closeRequerimientosModal() {
    document.getElementById("requerimientosModal").classList.remove("active");
    tramiteFormActual = null;
}

function confirmAddTramite() {
    if (tramiteFormActual) {
        tramiteFormActual.submit();
    }
}