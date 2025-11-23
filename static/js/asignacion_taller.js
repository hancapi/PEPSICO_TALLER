 // static/js/asignacion_taller.js
// ======================================================
//  Asignación de Vehículos — Programación de ingreso
//  Supervisor aprueba SolicitudesIngresoVehiculo
// ======================================================

// ======================================================
//  CSRF token
// ======================================================
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        for (let c of document.cookie.split(";")) {
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
//  Abrir / cerrar modal
// ======================================================
function abrirAsignacion(solicitudId, patente, fechaSolicitada) {
    document.getElementById("asig_solicitud_id").value = solicitudId;
    document.getElementById("asig_patente_txt").innerText = patente;
    document.getElementById("asig_fecha_solicitada_txt").innerText = fechaSolicitada;

    const inputFechaIng = document.getElementById("asig_fecha_ingreso");
    const inputHoraIng  = document.getElementById("asig_hora_ingreso");

    // Por defecto usamos la misma fecha solicitada
    if (inputFechaIng && !inputFechaIng.value) {
        inputFechaIng.value = fechaSolicitada;
    }

    // Hora por defecto
    if (inputHoraIng && !inputHoraIng.value) {
        inputHoraIng.value = "09:00";
    }

    document.getElementById("modalAsignacion").classList.remove("d-none");
}

function cerrarModal() {
    document.getElementById("modalAsignacion").classList.add("d-none");
}

// ======================================================
//  Recargar tabla de SOLICITUDES pendientes
// ======================================================
async function cargarPendientes() {
    const cont = document.getElementById("tablaAsignacionTaller");
    if (!cont) return;

    try {
        const resp = await fetch("/api/ordenestrabajo/supervisor/solicitudes/", {
            credentials: "same-origin"
        });

        const data = await resp.json();

        if (!data.success) {
            cont.innerHTML = `<tr><td colspan="6" class="text-danger">${data.message}</td></tr>`;
            return;
        }

        // La API devuelve HTML completo del tbody
        cont.innerHTML = data.html;

        // Volver a enlazar botones
        enlazarBotonesAsignar();

    } catch (err) {
        console.error(err);
        cont.innerHTML = `<tr><td colspan="6" class="text-danger">Error al cargar datos.</td></tr>`;
    }
}

// ======================================================
//  Enlaza botones luego del refresh dinámico
// ======================================================
function enlazarBotonesAsignar() {
    document.querySelectorAll(".btn-asignar").forEach((btn) => {
        btn.addEventListener("click", () => {
            abrirAsignacion(
                btn.dataset.solicitudId,
                btn.dataset.patente,
                btn.dataset.fechaSolicitada
            );
        });
    });
}

// ======================================================
//  Enviar aprobación de solicitud (crea OT)
// ======================================================
document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("formAsignacion");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const solicitud_id  = document.getElementById("asig_solicitud_id").value;
        const mecanico_rut  = document.getElementById("asig_mecanico").value;
        const comentario    = document.getElementById("asig_comentario").value.trim();
        const fecha_ingreso = document.getElementById("asig_fecha_ingreso").value;
        const hora_ingreso  = document.getElementById("asig_hora_ingreso").value;
        const modulo        = document.getElementById("asig_modulo").value;

        if (!fecha_ingreso) {
            alert("Debe indicar la fecha de ingreso al taller.");
            return;
        }
        if (!hora_ingreso) {
            alert("Debe indicar la hora de ingreso al taller.");
            return;
        }
        if (!comentario) {
            alert("Debe ingresar un comentario.");
            return;
        }
        if (!modulo) {
            alert("Debe seleccionar un módulo/pasillo del taller.");
            return;
        }

        const fd = new FormData();
        fd.append("solicitud_id", solicitud_id);
        fd.append("mecanico_rut", mecanico_rut);
        fd.append("comentario", comentario);
        fd.append("fecha", fecha_ingreso);
        fd.append("hora", hora_ingreso);
        fd.append("modulo", modulo);              // 👈 IMPORTANTE: enviar al backend

        try {
            const res = await fetch("/api/ordenestrabajo/supervisor/solicitud/aprobar/", {
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
                alert(data.message || "Error al aprobar la solicitud.");
                return;
            }

            alert("Solicitud aprobada y OT creada correctamente.");
            cerrarModal();

            // Recargar tabla sin refrescar pantalla
            cargarPendientes();

        } catch (err) {
            console.error(err);
            alert("Error de comunicación con el servidor.");
        }
    });

    // Inicial
    enlazarBotonesAsignar();
    cargarPendientes();

    // Auto refresh cada 10s
    setInterval(cargarPendientes, 10000);
});
