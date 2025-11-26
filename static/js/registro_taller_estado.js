// static/js/registro_taller_estado.js
// ======================================================
//  Actualización de estado de una OT (mecánico / supervisor)
//  - Usado en Registro Taller
// ======================================================

// CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        for (const c of document.cookie.split(";")) {
            const cookie = c.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie("csrftoken");


// ======================================================
//  Enviar cambio de estado al backend
//  (usa la API oficial: /api/ordenestrabajo/estado/cambiar/)
// ======================================================
async function enviarCambioEstado(patente, estado, comentario = "") {

    const comentarioTrim = (comentario || "").trim();
    if (!comentarioTrim) {
        alert("Debe ingresar un comentario para cambiar el estado.");
        return;
    }

    const fd = new FormData();
    fd.append("patente", patente);
    fd.append("estado", estado);
    fd.append("comentario", comentarioTrim);

    try {
        const res = await fetch("/api/ordenestrabajo/estado/cambiar/", {
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
            // Función definida en registro_taller.js
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

    // ✔ Botón RECIBIR  (Pendiente -> En Taller)
    if (e.target.classList.contains("btn-recibir")) {
        const patente = e.target.dataset.patente;
        const comentario = prompt("Ingrese comentario obligatorio para RECIBIR la OT en el taller:");
        if (!comentario || comentario.trim() === "") {
            alert("Debe ingresar un comentario.");
            return;
        }
        enviarCambioEstado(patente, "En Taller", comentario);
        return;
    }

    // ✔ Botón FINALIZAR
    if (e.target.classList.contains("btn-finalizar")) {
        const patente = e.target.dataset.patente;
        const comentario = prompt("Ingrese comentario obligatorio para FINALIZAR la OT:");
        if (!comentario || comentario.trim() === "") {
            alert("Debe ingresar un comentario.");
            return;
        }
        enviarCambioEstado(patente, "Finalizado", comentario);
        return;
    }

    // ✔ Botón PAUSAR
    if (e.target.classList.contains("btn-pausar")) {
        const patente = e.target.dataset.patente;
        const comentario = prompt("Ingrese comentario obligatorio para PAUSAR la OT:");
        if (!comentario || comentario.trim() === "") {
            alert("Debe ingresar un comentario.");
            return;
        }
        enviarCambioEstado(patente, "Pausado", comentario);
        return;
    }

    // ✔ Botón REANUDAR (volver a En Proceso)
    if (e.target.classList.contains("btn-reanudar")) {
        const patente = e.target.dataset.patente;
        const comentario = prompt("Ingrese comentario obligatorio para REANUDAR la OT:");
        if (!comentario || comentario.trim() === "") {
            alert("Debe ingresar un comentario.");
            return;
        }
        enviarCambioEstado(patente, "En Proceso", comentario);
        return;
    }

});
