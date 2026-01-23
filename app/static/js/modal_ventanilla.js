const btnFinalizar = document.getElementById("btn-finalizar");
const modalFinalizar = document.getElementById("modal-finalizar");
const btnCerrarFinalizar = document.getElementById("btn-cancelar-modal");

btnFinalizar?.addEventListener("click", () => modalFinalizar.classList.add("activo"));
btnCerrarFinalizar?.addEventListener("click", () => modalFinalizar.classList.remove("activo"));

modalFinalizar?.addEventListener("click", e => {
    if (e.target === modalFinalizar) modalFinalizar.classList.remove("activo");
});

const btnCancelar = document.getElementById("btn-cancelar-tramite");
const modalCancelar = document.getElementById("modal-cancelar");
const btnCerrarCancelar = document.getElementById("btn-cancelar-modal-cancelar");

btnCancelar?.addEventListener("click", () => modalCancelar.classList.add("activo"));
btnCerrarCancelar?.addEventListener("click", () => modalCancelar.classList.remove("activo"));

modalCancelar?.addEventListener("click", e => {
    if (e.target === modalCancelar) modalCancelar.classList.remove("activo");
});

const selectMotivo = document.getElementById("motivo_cancelacion");
const contenedorOtro = document.getElementById("motivo-otro-container");
const textareaOtro = document.getElementById("motivo_otro");

selectMotivo?.addEventListener("change", () => {
    if (selectMotivo.value === "otro") {
        contenedorOtro.style.display = "block";
        textareaOtro.required = true;
    } else {
        contenedorOtro.style.display = "none";
        textareaOtro.required = false;
        textareaOtro.value = "";
    }
});