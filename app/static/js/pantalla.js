const socket = io();

socket.on("connect", () => {
    console.log("Pantalla conectada a WebSocket");
});

socket.on("turnos_en_espera", (turnos) => {
    const lista = document.getElementById("esperaLista");
    if (!lista) return;

    lista.innerHTML = "";

    if (!turnos || turnos.length === 0) {
        const p = document.createElement("p");
        p.className = "texto-secundario";
        p.textContent = "No hay turnos en espera";
        lista.appendChild(p);
        return;
    }

    turnos.forEach(t => {
        const card = document.createElement("div");
        card.className = "turno-card-pequeno";

        const span = document.createElement("span");
        span.className = "numero-pequeno";
        span.textContent = t;

        card.appendChild(span);
        lista.appendChild(card);
    });

    activarCarrusel(lista);
});

socket.on("turnos_en_llamado", (turnos) => {
    const grid = document.getElementById("llamadoGrid");
    if (!grid) return;

    grid.innerHTML = "";

    if (!turnos || turnos.length === 0) {
        const div = document.createElement("div");
        div.className = "sin-turnos";

        const p = document.createElement("p");
        p.textContent = "No hay turnos en llamado";

        div.appendChild(p);
        grid.appendChild(div);
        return;
    }

    turnos.forEach(t => {
        const card = document.createElement("div");
        card.className = "turno-card";

        const numero = document.createElement("div");
        numero.className = "turno-numero";
        numero.textContent = `Turno ${t.turno}`;

        const info = document.createElement("div");
        info.className = "turno-info";

        const ventanilla = document.createElement("span");
        ventanilla.className = "turno-ventanilla";
        ventanilla.textContent = t.ventanilla;

        info.appendChild(ventanilla);
        card.appendChild(numero);
        card.appendChild(info);

        grid.appendChild(card);
    });
});

function activarCarrusel(lista) {
    const items = lista.querySelectorAll('.turno-card-pequeno');
    if (items.length === 0) return;

    lista.classList.remove("carousel");

    let totalWidth = 0;
    items.forEach(item => {
        totalWidth += item.offsetWidth + 8;
    });

    const containerWidth = lista.parentElement.clientWidth;

    if (totalWidth > containerWidth) {
        const fragment = document.createDocumentFragment();
        items.forEach(item => {
            fragment.appendChild(item.cloneNode(true));
        });
        lista.appendChild(fragment);
        lista.classList.add("carousel");
    }
}

const adVideo = document.getElementById("ad-video");
const adImage = document.getElementById("ad-image");

const FALLBACK_MS = 600;

let videoRevealTimer = null;

function revelarVideo() {
    if (videoRevealTimer) {
        clearTimeout(videoRevealTimer);
        videoRevealTimer = null;
    }
    adVideo.style.display = "block";
}

socket.on("anuncio_play", (a) => {
    if (videoRevealTimer) {
        clearTimeout(videoRevealTimer);
        videoRevealTimer = null;
    }

    adVideo.removeEventListener("playing", revelarVideo);
    adVideo.pause();
    adVideo.currentTime = 0;
    adVideo.style.display = "none";
    adImage.style.display = "none";

    if (a.tipo === "video") {
        adVideo.src = a.enlace;
        adVideo.load();

        const reproducir = () => {
            adVideo.addEventListener("playing", revelarVideo, { once: true });

            videoRevealTimer = setTimeout(revelarVideo, FALLBACK_MS);

            adVideo.play().catch(() => {
                console.log("No se pudo reproducir el video automáticamente");
                revelarVideo();
            });
        };

        const iniciar = () => {
            const delay = (a.play_at * 1000) - Date.now();

            if (delay > 0) {
                setTimeout(reproducir, delay);
            } else {
                reproducir();
            }
        };

        if (adVideo.readyState >= 3) {
            iniciar();
        } else {
            adVideo.addEventListener(
                "canplay",
                iniciar,
                { once: true }
            );
        }

    } else {
        const delay = (a.play_at * 1000) - Date.now();

        const mostrarImagen = () => {

            const pre = new Image();

            pre.onload = () => {
                adImage.src = a.enlace;
                adImage.style.display = "block";
            };

            pre.onerror = () => {
                console.log("No se pudo cargar la imagen del anuncio");
            };

            pre.src = a.enlace;
        };

        if (delay > 0) {
            setTimeout(mostrarImagen, delay);
        } else {
            mostrarImagen();
        }
    }
});

socket.on("anuncio_clear", () => {
    if (videoRevealTimer) {
        clearTimeout(videoRevealTimer);
        videoRevealTimer = null;
    }

    adVideo.removeEventListener("playing", revelarVideo);
    adVideo.pause();
    adVideo.style.display = "none";
    adImage.style.display = "none";
});