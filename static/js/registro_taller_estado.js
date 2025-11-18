// static/js/registro_taller_estado.js
// ======================================================
//  Actualización de estado de una OT (mecánico / supervisor)
// ======================================================

// CSRF
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
//  Enviar cambio de estado al backend
//  (usa la API oficial: /api/ordenestrabajo/cambiar-estado/)
// ======================================================
async function enviarCambioEstado(patente, estado, comentario = "") {

    const fd = new FormData();
    fd.append("patente", patente);
    fd.append("estado", estado);
    fd.append("comentario", comentario);

    try {
        // 🔁 Antes: POST a window.location.pathname (/registro-taller/)
        // Ahora: POST a la API de cambio de estado
        const res = await fetch("/registro-taller/", {
            method: "POST",
            body: fd,
            headers: {
                "X-CSRFToken": csrftoken,
                "X-Requested-With": "XMLHttpRequest"
            },
            credentials: "same-origin"
        });

        const data = await res.json();

        if (!data.success) {
            alert(data.message || "Error al actualizar estado.");
            return;
        }

        if (typeof cargarVehiculos === "function") {
            cargarVehiculos(); // refresca tabla principal
        }
        alert("Estado actualizado correctamente.");

    } catch (err) {
        alert("❌ Error al actualizar estado.");
        console.error(err);
    }
}


// ======================================================
//  Capturar clicks en botones de acción
// ======================================================
document.addEventListener("click", (e) => {

    // ✔ Botón FINALIZAR
    if (e.target.classList.contains("btn-finalizar")) {

        const patente = e.target.dataset.patente;
        const comentario = prompt("Ingrese comentario obligatorio para finalizar:");

        if (!comentario || comentario.trim() === "") {
            alert("Debe ingresar un comentario.");
            return;
        }

        enviarCambioEstado(patente, "Finalizado", comentario);
    }

    // ✔ Botón PAUSAR
    if (e.target.classList.contains("btn-pausar")) {
        const patente = e.target.dataset.patente;
        enviarCambioEstado(patente, "Pausado");
    }

    // ✔ Botón REANUDAR
    if (e.target.classList.contains("btn-reanudar")) {
        const patente = e.target.dataset.patente;
        enviarCambioEstado(patente, "En Proceso");
    }

});
