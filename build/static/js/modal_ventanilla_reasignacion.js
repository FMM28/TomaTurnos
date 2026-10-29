let formSubmitting = false;

function openReasignarModal(idTramite, nombre) {
    formSubmitting = false;
    
    document.getElementById("modalIdTramite").value = idTramite;
    document.getElementById("modalTramiteNombre").innerText = nombre;
    
    const btnConfirmar = document.getElementById("btnConfirmar");
    btnConfirmar.disabled = false;
    btnConfirmar.textContent = "Confirmar reasignación";
    
    document.getElementById("reasignarModal").classList.add("active");
}

function closeReasignarModal() {
    document.getElementById("reasignarModal").classList.remove("active");
    
    document
        .querySelectorAll('input[name="tipo_reasignacion"]')
        .forEach(radio => radio.checked = false);
    
    formSubmitting = false;
    
    const btnConfirmar = document.getElementById("btnConfirmar");
    btnConfirmar.disabled = false;
    btnConfirmar.textContent = "Confirmar reasignación";
}

document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("reasignarForm");
    const btnConfirmar = document.getElementById("btnConfirmar");
    
    form.addEventListener("submit", function(e) {
        if (formSubmitting) {
            e.preventDefault();
            return false;
        }
        
        const tipoSeleccionado = document.querySelector('input[name="tipo_reasignacion"]:checked');
        if (!tipoSeleccionado) {
            e.preventDefault();
            alert("Por favor selecciona un tipo de reasignación");
            return false;
        }
        
        formSubmitting = true;
        
        btnConfirmar.disabled = true;
        btnConfirmar.textContent = "Procesando...";
        
        return true;
    });
});

document.getElementById("reasignarModal").addEventListener("click", function(e) {
    if (e.target === this) {
        closeReasignarModal();
    }
});