document.addEventListener("DOMContentLoaded", () => {
    const areaCards = document.querySelectorAll(".area-card");

    let maxConcurrencia = -1;
    let cardsMasCargadas = [];

    areaCards.forEach(card => {
        const espera = parseInt(card.querySelector(".espera")?.textContent || 0);
        const atendiendo = parseInt(card.querySelector(".atendiendo")?.textContent || 0);
        const concurrencia = espera + atendiendo;

        if (concurrencia > maxConcurrencia) {
            maxConcurrencia = concurrencia;
            cardsMasCargadas = [card];
        } else if (concurrencia === maxConcurrencia) {
            cardsMasCargadas.push(card);
        }
    });

    cardsMasCargadas.forEach(card => {
        card.classList.add("highlight");
    });
});