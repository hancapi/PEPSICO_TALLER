// static/js/registro_taller.js
// ======================================================
//  REGISTRO TALLER — Auto refresh de vehículos en taller
//  - Mecánico / Supervisor
//  - Usa /api/ordenestrabajo/... para cargar OTs
//  - Los cambios de estado los maneja registro_taller_estado.js
// ======================================================

document.addEventListener("DOMContentLoaded", () => {
    cargarVehiculos();                   // Carga inicial
    setInterval(cargarVehiculos, 10000); // 🔁 Refresco cada 10 segundos
});

// ======================================================
//  Cargar vehículos según el modo (mecánico / supervisor)
// ======================================================
async function cargarVehiculos() {
    const contenedor = document.getElementById("tablaVehiculosTaller");
    const modoWrapper = document.querySelector("#modoWrapper");
    const modo = modoWrapper?.dataset.modo || "mecanico";

    if (!contenedor) return;

    contenedor.innerHTML = "<p>Cargando vehículos asignados...</p>";

    const API_URL =
        modo === "supervisor"
            ? "/api/ordenestrabajo/supervisor/vehiculos/"
            : "/api/ordenestrabajo/mecanico/vehiculos/";

    try {
        const resp = await fetch(API_URL, { credentials: "same-origin" });
        const data = await resp.json();

        if (!data.success) {
            contenedor.innerHTML = `<p class="text-danger">Error: ${data.message}</p>`;
            return;
        }

        // La API devuelve HTML listo para el <tbody>
        contenedor.innerHTML = data.html;

        // 👇 Los botones de estado (recibir / pausar / finalizar / reanudar)
        // se manejan en registro_taller_estado.js mediante event delegation.

    } catch (error) {
        console.error(error);
        contenedor.innerHTML = `<p class="text-danger">Error inesperado al cargar datos.</p>`;
    }
}
