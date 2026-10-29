document.addEventListener("DOMContentLoaded", () => {
    const roleSelect = document.getElementById("role");
    const areaSelect = document.getElementById("area");

    let hiddenArea = document.getElementById("area_hidden");
    if (!hiddenArea) {
        hiddenArea = document.createElement("input");
        hiddenArea.type = "hidden";
        hiddenArea.name = "area";
        hiddenArea.id = "area_hidden";
        areaSelect.parentNode.appendChild(hiddenArea);
    }

    roleSelect.addEventListener("change", toggleArea);

    toggleArea();
});

function toggleArea() {
        if (roleSelect.value === "admin") {
            areaSelect.disabled = true;
            areaSelect.required = false;
            areaSelect.value = "";

            hiddenArea.value = "";
        } else {
            areaSelect.disabled = false;
            areaSelect.required = true;
            hiddenArea.value = "";
        }
    }