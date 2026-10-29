function toggleArea(element)
{
    const checkbox = element.querySelector("input");

    checkbox.checked = !checkbox.checked;

    element.classList.toggle("selected", checkbox.checked);
}

function toggleMetric(element)
{
    const checkbox = element.querySelector("input");

    checkbox.checked = !checkbox.checked;

    element.classList.toggle("selected", checkbox.checked);
}



document.addEventListener("DOMContentLoaded", function()
{

    const form = document.getElementById("reportForm");

    const btnGenerate =
        document.getElementById("btnGenerate");

    const today =
        new Date().toISOString().split("T")[0];

    document.getElementById("fecha_inicio").max = today;
    document.getElementById("fecha_fin").max = today;

    const formatCards =
        document.querySelectorAll(".format-card");

    formatCards.forEach(card =>
    {
        card.addEventListener("click", function()
        {
            formatCards.forEach(c =>
                c.classList.remove("selected")
            );

            card.classList.add("selected");

            card.querySelector("input").checked = true;
        });
    });

    document
    .getElementById("btnSelectAllAreas")
    .onclick = () =>
    {
        document.querySelectorAll("input[name='area_ids']")
        .forEach(c =>
        {
            c.checked = true;
            c.closest(".metric-option")
             .classList.add("selected");
        });
    };


    document
    .getElementById("btnDeselectAllAreas")
    .onclick = () =>
    {
        document.querySelectorAll("input[name='area_ids']")
        .forEach(c =>
        {
            c.checked = false;
            c.closest(".metric-option")
             .classList.remove("selected");
        });
    };

    document
    .getElementById("btnSelectAllMetrics")
    .onclick = () =>
    {
        document.querySelectorAll("input[name='metricas']")
        .forEach(c =>
        {
            c.checked = true;
            c.closest(".metric-option")
             .classList.add("selected");
        });
    };


    document
    .getElementById("btnDeselectAllMetrics")
    .onclick = () =>
    {
        document.querySelectorAll("input[name='metricas']")
        .forEach(c =>
        {
            c.checked = false;
            c.closest(".metric-option")
             .classList.remove("selected");
        });
    };

    form.addEventListener("submit", function(e)
    {

        const areas =
            document.querySelectorAll(
                "input[name='area_ids']:checked"
            ).length;

        if (areas === 0)
        {
            alert("Selecciona al menos un área");
            e.preventDefault();
            return;
        }


        const metrics =
            document.querySelectorAll(
                "input[name='metricas']:checked"
            ).length;

        if (metrics === 0)
        {
            alert("Selecciona al menos una métrica");
            e.preventDefault();
            return;
        }


        btnGenerate.disabled = true;

        btnGenerate.innerText =
            "Generando reporte...";


        window.addEventListener("focus", function restore()
        {
            btnGenerate.disabled = false;

            btnGenerate.innerText =
                "Generar Reporte";

            window.removeEventListener("focus", restore);
        });

    });

});