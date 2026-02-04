document.addEventListener("DOMContentLoaded", () => {

    const fileInput = document.getElementById("archivo");
    const tituloInput = document.getElementById("titulo");
    const tipoInput = document.getElementById("tipo");
    const duracionInput = document.getElementById("duracion");

    const previewBox = document.getElementById("preview-box");
    const videoPreview = document.getElementById("video-preview");
    const previewTitulo = document.getElementById("preview-titulo");
    const previewDuracion = document.getElementById("preview-duracion");

    fileInput.addEventListener("change", () => {
        const file = fileInput.files[0];
        if (!file) return;

        if (file.type.startsWith("video/")) {
            tipoInput.value = "video";
        } else if (file.type.startsWith("image/")) {
            tipoInput.value = "imagen";
            duracionInput.value = 5;
            return;
        }

        const nombreLimpio = file.name
            .replace(/\.[^/.]+$/, "")
            .replace(/[_\-]+/g, " ")
            .replace(/\s+/g, " ")
            .trim();

        tituloInput.value = nombreLimpio;

        const url = URL.createObjectURL(file);
        videoPreview.src = url;

        videoPreview.onloadedmetadata = () => {
            const duracion = Math.ceil(videoPreview.duration || 5);
            duracionInput.value = duracion;

            previewTitulo.textContent = nombreLimpio;
            previewDuracion.textContent = duracion;

            previewBox.style.display = "block";
        };

        videoPreview.onerror = () => {
            duracionInput.value = 5;
            previewTitulo.textContent = nombreLimpio;
            previewDuracion.textContent = "5";
            previewBox.style.display = "block";
        };
    });

});