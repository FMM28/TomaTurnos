const modal = document.getElementById("reasignarModal");
const tramiteNombreSpan = document.getElementById("modalTramiteNombre");
const tramiteIdInput = document.getElementById("modalIdTramite");
const referenciaSelect = document.getElementById("referenciaSelect");
const radios = document.querySelectorAll("input[name='posicion_tipo']");

function openReasignarModal(idTramite, nombreTramite) {

    tramiteNombreSpan.textContent = nombreTramite;
    tramiteIdInput.value = idTramite;

    modal.style.display = "flex";
}

function closeReasignarModal() {
    modal.style.display = "none";
}

window.addEventListener("click", function (event) {
    if (event.target === modal) {
        closeReasignarModal();
    }
});

function actualizarEstadoReferencia() {

    const seleccion = document.querySelector("input[name='posicion_tipo']:checked");

    if (!seleccion) return;

    if (seleccion.value === "antes" || seleccion.value === "despues") {
        referenciaSelect.disabled = false;
        referenciaSelect.required = true;
    } else {
        referenciaSelect.disabled = true;
        referenciaSelect.required = false;
        referenciaSelect.value = "";
    }
}

radios.forEach(radio => {
    radio.addEventListener("change", actualizarEstadoReferencia);
});

document.addEventListener("DOMContentLoaded", function () {
    actualizarEstadoReferencia();
});
