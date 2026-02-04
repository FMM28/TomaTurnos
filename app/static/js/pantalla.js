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
        div.innerHTML = "<p>No hay turnos en llamado</p>";
        grid.appendChild(div);
        return;
    }

    turnos.forEach(t => {
        const card = document.createElement("div");
        card.className = "turno-card";

        card.innerHTML = `
            <div class="turno-numero">Turno ${t.turno}</div>
            <div class="turno-info">
                <span class="turno-ventanilla">${t.ventanilla}</span>
            </div>
        `;

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

socket.on("anuncio_play", (a) => {
    adVideo.pause();
    adVideo.style.display = "none";
    adImage.style.display = "none";

    if (a.tipo === "video") {
        adVideo.src = a.enlace;
        adVideo.style.display = "block";
        adVideo.play().catch(() => {
            console.log("No se pudo reproducir el video automáticamente");
        });
    } else {
        adImage.src = a.enlace;
        adImage.style.display = "block";
    }
});

socket.on("anuncio_clear", () => {
    adVideo.pause();
    adVideo.style.display = "none";
    adImage.style.display = "none";
});