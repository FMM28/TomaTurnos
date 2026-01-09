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