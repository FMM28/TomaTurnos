document.addEventListener("DOMContentLoaded", () => {

    const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100 MB
    const MAX_FILE_SIZE_MB = 100;

    const fileInput = document.getElementById("archivo");
    const tituloInput = document.getElementById("titulo");
    const tipoInput = document.getElementById("tipo");
    const duracionInput = document.getElementById("duracion");
    const duracionGroup = document.getElementById("duracion-group");

    const previewBox = document.getElementById("preview-box");
    const videoPreview = document.getElementById("video-preview");
    const imagePreview = document.getElementById("image-preview");
    const previewTitulo = document.getElementById("preview-titulo");
    const previewTipo = document.getElementById("preview-tipo");
    const previewDuracion = document.getElementById("preview-duracion");
    const previewDuracionContainer = document.getElementById("preview-duracion-container");

    const archivoGroup = document.getElementById("archivo-group");
    const modo = archivoGroup.dataset.modo;
    const duracionExistente = archivoGroup.dataset.duracion;
    const tipoExistente = archivoGroup.dataset.tipo;
    const archivoUrl = archivoGroup.dataset.archivoUrl;

    // Elemento para mostrar tamaño
    const sizeInfo = document.createElement("small");
    sizeInfo.id = "file-size-info";
    sizeInfo.className = "form-hint";
    sizeInfo.style.display = "block";
    sizeInfo.style.marginTop = "5px";
    archivoGroup.appendChild(sizeInfo);

    if (modo === 'edit' && tipoExistente) {
        loadExistingPreview(tipoExistente, archivoUrl, tituloInput.value, duracionExistente);
    }

    fileInput.addEventListener("change", () => {

        const file = fileInput.files[0];

        if (!file) {
            sizeInfo.textContent = "";
            if (modo === 'edit' && tipoExistente) {
                loadExistingPreview(tipoExistente, archivoUrl, tituloInput.value, duracionExistente);
            } else {
                resetPreview();
            }
            return;
        }

        // Mostrar tamaño
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        sizeInfo.textContent = `Tamaño del archivo: ${sizeMB} MB`;

        // Validar límite
        if (file.size > MAX_FILE_SIZE) {

            sizeInfo.style.color = "red";
            sizeInfo.textContent = `El archivo pesa ${sizeMB} MB. Máximo permitido: ${MAX_FILE_SIZE_MB} MB`;

            fileInput.value = "";
            resetPreview();

            alert(`El archivo excede el límite de ${MAX_FILE_SIZE_MB} MB`);

            return;
        }

        sizeInfo.style.color = "green";

        const nombreLimpio = file.name
            .replace(/\.[^/.]+$/, "")
            .replace(/[_\-]+/g, " ")
            .replace(/\s+/g, " ")
            .trim();

        tituloInput.value = nombreLimpio;

        if (file.type.startsWith("video/")) {
            handleVideoFile(file, nombreLimpio);
        } else if (file.type.startsWith("image/")) {
            handleImageFile(file, nombreLimpio);
        }
    });

    duracionInput.addEventListener("input", () => {
        if (tipoInput.value === "imagen") {
            previewDuracion.textContent = duracionInput.value;
        }
    });

    tituloInput.addEventListener("input", () => {
        if (previewBox.style.display !== "none") {
            previewTitulo.textContent = tituloInput.value;
        }
    });

    function loadExistingPreview(tipo, url, titulo, duracion) {
        tipoInput.value = tipo;

        if (tipo === "video") {
            if (url) {
                videoPreview.src = url;
                videoPreview.style.display = "block";
                imagePreview.style.display = "none";

                videoPreview.onloadedmetadata = () => {
                    const videoDuracion = Math.ceil(videoPreview.duration || duracion || 5);
                    duracionInput.value = videoDuracion;

                    previewTitulo.textContent = titulo;
                    previewTipo.textContent = "Video";
                    previewDuracion.textContent = videoDuracion;
                    previewDuracionContainer.style.display = "block";

                    duracionGroup.style.display = "none";
                    duracionInput.removeAttribute("required");

                    previewBox.style.display = "block";
                };

                videoPreview.onerror = () => {
                    previewTitulo.textContent = titulo;
                    previewTipo.textContent = "Video";
                    previewDuracion.textContent = duracion || 5;
                    previewDuracionContainer.style.display = "block";
                    duracionGroup.style.display = "none";
                    previewBox.style.display = "block";
                };
            }
        } else if (tipo === "imagen") {
            if (url) {
                imagePreview.src = url;
                imagePreview.style.display = "block";
                videoPreview.style.display = "none";
            }

            duracionInput.value = duracion || 5;
            duracionGroup.style.display = "block";
            duracionInput.setAttribute("required", "required");

            previewTitulo.textContent = titulo;
            previewTipo.textContent = "Imagen";
            previewDuracion.textContent = duracionInput.value;
            previewDuracionContainer.style.display = "block";

            previewBox.style.display = "block";
        }
    }

    function handleVideoFile(file, nombreLimpio) {
        tipoInput.value = "video";
        duracionGroup.style.display = "none";
        duracionInput.removeAttribute("required");

        const url = URL.createObjectURL(file);
        videoPreview.src = url;
        videoPreview.style.display = "block";
        imagePreview.style.display = "none";

        videoPreview.onloadedmetadata = () => {
            const duracion = Math.ceil(videoPreview.duration || 5);
            duracionInput.value = duracion;

            previewTitulo.textContent = nombreLimpio;
            previewTipo.textContent = "Video";
            previewDuracion.textContent = duracion;
            previewDuracionContainer.style.display = "block";

            previewBox.style.display = "block";
        };

        videoPreview.onerror = () => {
            duracionInput.value = 5;
            showPreview(nombreLimpio, "Video", "5");
        };
    }

    function handleImageFile(file, nombreLimpio) {
        tipoInput.value = "imagen";

        const duracionActual = duracionInput.value || 5;
        duracionInput.value = duracionActual;
        duracionGroup.style.display = "block";
        duracionInput.setAttribute("required", "required");

        const url = URL.createObjectURL(file);
        imagePreview.src = url;
        imagePreview.style.display = "block";
        videoPreview.style.display = "none";

        imagePreview.onload = () => {
            showPreview(nombreLimpio, "Imagen", duracionInput.value);
        };
    }

    function showPreview(titulo, tipo, duracion) {
        previewTitulo.textContent = titulo;
        previewTipo.textContent = tipo;
        previewDuracion.textContent = duracion;
        previewDuracionContainer.style.display = "block";
        previewBox.style.display = "block";
    }

    function resetPreview() {
        previewBox.style.display = "none";
        duracionGroup.style.display = "none";
        videoPreview.style.display = "none";
        imagePreview.style.display = "none";
        videoPreview.src = "";
        imagePreview.src = "";
        tipoInput.value = "";
        duracionInput.value = "";
        duracionInput.removeAttribute("required");
    }
});


document.addEventListener('DOMContentLoaded', function() {

    const MAX_FILE_SIZE = 100 * 1024 * 1024;

    const form = document.querySelector('.form-card form');
    const submitButton = form.querySelector('button[type="submit"]');
    const fileInput = document.getElementById("archivo");

    const processingMessage = document.createElement('div');
    processingMessage.id = 'processing-message';
    processingMessage.style.marginTop = '15px';
    processingMessage.style.padding = '10px';
    processingMessage.style.backgroundColor = '#f0f0f0';
    processingMessage.style.border = '1px solid #ccc';
    processingMessage.style.borderRadius = '5px';
    processingMessage.style.color = '#333';
    processingMessage.style.fontWeight = 'bold';
    processingMessage.style.display = 'none';
    processingMessage.textContent = 'Se está procesando su archivo, por favor espere...';

    form.appendChild(processingMessage);

    form.addEventListener('submit', function(e) {

        const file = fileInput.files[0];

        if (file && file.size > MAX_FILE_SIZE) {
            alert("El archivo excede el límite de 100 MB.");
            e.preventDefault();
            return;
        }

        submitButton.disabled = true;
        processingMessage.style.display = 'block';
    });

});
