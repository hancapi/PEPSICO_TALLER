document.addEventListener("DOMContentLoaded", () => {
    cargarVehiculos();
});

async function cargarVehiculos() {

    const contenedor = document.getElementById("tablaVehiculosTaller");
    const modo = document.querySelector("#modoWrapper")?.dataset.modo || "mecanico";

    if (!contenedor) return;

    contenedor.innerHTML = "<p>Cargando vehículos asignados...</p>";

    // API correcta según perfil
    const API_URL =
        modo === "supervisor"
            ? "/api/ordenestrabajo/supervisor/vehiculos/"
            : "/api/ordenestrabajo/mecanico/vehiculos/";

    try {
        const resp = await fetch(API_URL);
        const data = await resp.json();

        if (!data.success) {
            contenedor.innerHTML = `<p class="text-danger">Error: ${data.message}</p>`;
            return;
        }

        contenedor.innerHTML = data.html;

    } catch (error) {
        contenedor.innerHTML = `<p class="text-danger">Error inesperado al cargar datos.</p>`;
        console.error(error);
    }
}
