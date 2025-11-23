// static/js/registro_taller.js
// ======================================================
//  REGISTRO TALLER — Auto refresh + cambios de estado
//  - Mecánico / Supervisor
//  - Usa /api/ordenestrabajo/... para cargar y actualizar OTs
// ======================================================

document.addEventListener("DOMContentLoaded", () => {
    cargarVehiculos();                   // Carga inicial
    setInterval(cargarVehiculos, 10000); // 🔁 Refresco cada 10 segundos
});


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
const csrftoken = getCookie("csrftoken");


// ======================================================
//  Helper: pedir comentario obligatorio
// ======================================================
function pedirComentario(mensaje) {
    const txt = prompt(mensaje || "Ingrese comentario para el cambio de estado:");
    if (!txt || txt.trim() === "") {
        alert("Debe ingresar un comentario.");
        return null;
    }
    return txt.trim();
}


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

        // 🔥 Muy importante: volver a enlazar botones cada vez que se re-renderiza la tabla
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

    // RECIBIR (Pendiente -> Recibida)
    document.querySelectorAll(".btn-recibir").forEach((btn) => {
        btn.addEventListener("click", () => {
            const patente = btn.dataset.patente;

            // Puedes dejar el texto fijo o también pedir comentario aquí.
            const comentario = pedirComentario("Comentario al recibir el vehículo en taller:");
            if (!comentario) return;

            enviarCambioEstado(patente, "Recibida", comentario);
        });
    });

    // FINALIZAR
    document.querySelectorAll(".btn-finalizar").forEach((btn) => {
        btn.addEventListener("click", () => {
            const patente = btn.dataset.patente;
            const comentario = pedirComentario("Ingrese comentario obligatorio para finalizar:");
            if (!comentario) return;

            enviarCambioEstado(patente, "Finalizado", comentario);
        });
    });

    // PAUSAR
    document.querySelectorAll(".btn-pausar").forEach((btn) => {
        btn.addEventListener("click", () => {
            const patente = btn.dataset.patente;
            const comentario = pedirComentario("Motivo de pausa de la OT:");
            if (!comentario) return;

            enviarCambioEstado(patente, "Pausado", comentario);
        });
    });

    // REANUDAR (Recibida / Pausado / En Taller -> En Proceso)
    document.querySelectorAll(".btn-reanudar").forEach((btn) => {
        btn.addEventListener("click", () => {
            const patente = btn.dataset.patente;
            const comentario = pedirComentario("Comentario para reanudar (qué se hará ahora):");
            if (!comentario) return;

            enviarCambioEstado(patente, "En Proceso", comentario);
        });
    });
}


// ======================================================
//  API Cambio Estado (usa /api/ordenestrabajo/estado/cambiar/)
// ======================================================
async function enviarCambioEstado(patente, estado, comentario = "") {

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

        // 🔁 Refrescar la página completa para ver el estado real
        window.location.reload();

    } catch (err) {
        console.error(err);
        alert("❌ Error al actualizar estado.");
    }
}
