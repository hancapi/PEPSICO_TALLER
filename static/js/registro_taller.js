// static/js/registro_taller.js
// ======================================================
//  REGISTRO TALLER — Auto refresh + cambios de estado
// ======================================================

document.addEventListener("DOMContentLoaded", () => {
    cargarVehiculos();                 // carga inicial
    setInterval(cargarVehiculos, 10000); // 🔁 refresco cada 10 segundos
});


// ======================================================
//  Cargar vehículos según el modo (mecánico / supervisor)
// ======================================================
async function cargarVehiculos() {

    const contenedor = document.getElementById("tablaVehiculosTaller");
    const modo = document.querySelector("#modoWrapper")?.dataset.modo || "mecanico";

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

        contenedor.innerHTML = data.html;

        // 🔥 Muy importante: volver a enlazar botones
        enlazarBotonesCambioEstado();

    } catch (error) {
        contenedor.innerHTML = `<p class="text-danger">Error inesperado al cargar datos.</p>`;
        console.error(error);
    }
}



// ======================================================
//  Enlazar botones para cambio de estado
// ======================================================
function enlazarBotonesCambioEstado() {

    // FINALIZAR
    document.querySelectorAll(".btn-finalizar").forEach((btn) => {
        btn.addEventListener("click", () => {
            const patente = btn.dataset.patente;
            const comentario = prompt("Ingrese comentario obligatorio para finalizar:");

            if (!comentario || comentario.trim() === "") {
                alert("Debe ingresar un comentario.");
                return;
            }

            enviarCambioEstado(patente, "Finalizado", comentario);
        });
    });

    // PAUSAR
    document.querySelectorAll(".btn-pausar").forEach((btn) => {
        btn.addEventListener("click", () => {
            enviarCambioEstado(btn.dataset.patente, "Pausado");
        });
    });

    // REANUDAR
    document.querySelectorAll(".btn-reanudar").forEach((btn) => {
        btn.addEventListener("click", () => {
            enviarCambioEstado(btn.dataset.patente, "En Proceso");
        });
    });
}



// ======================================================
//  API Cambio Estado (usa /api/ordenestrabajo/estado/cambiar/)
// ======================================================
async function enviarCambioEstado(patente, estado, comentario = "") {

    const csrftoken = getCookie("csrftoken");

    const fd = new FormData();
    fd.append("patente", patente);
    fd.append("estado", estado);
    fd.append("comentario", comentario);

    try {
        const res = await fetch("/api/ordenestrabajo/estado/cambiar/", {
            method: "POST",
            body: fd,
            credentials: "same-origin",
            headers: {
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest"
            }
        });

        const data = await res.json();

        if (!data.success) {
            alert(data.message || "Error al actualizar estado.");
            return;
        }

        alert("Estado actualizado correctamente.");

        // 🔁 Refrescar la tabla inmediatamente
        cargarVehiculos();

    } catch (err) {
        console.error(err);
        alert("❌ Error al actualizar estado.");
    }
}



// ======================================================
//  Helper CSRF
// ======================================================
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        for (const cookie of document.cookie.split(";")) {
            const c = cookie.trim();
            if (c.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(c.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
