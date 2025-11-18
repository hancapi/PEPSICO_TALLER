// static/js/asignacion_taller.js
// ======================================================
//  Asignación de Vehículos — Taller PepsiCo (Dinámico)
// ======================================================


// ======================================================
//  CSRF token seguro
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
function abrirAsignacion(ot_id, patente) {
    document.getElementById("asig_ot_id").value = ot_id;
    document.getElementById("asig_patente_txt").innerText = patente;
    document.getElementById("modalAsignacion").classList.remove("d-none");
}

function cerrarModal() {
    document.getElementById("modalAsignacion").classList.add("d-none");
}


// ======================================================
//  Recargar tabla de asignaciones (AUTO-REFRESH)
// ======================================================
async function cargarPendientes() {

    const cont = document.getElementById("tablaAsignacionTaller");
    if (!cont) return;

    try {
        const resp = await fetch("/api/ordenestrabajo/supervisor/vehiculos/", {
            credentials: "same-origin"
        });

        const data = await resp.json();

        if (!data.success) {
            cont.innerHTML = `<tr><td colspan="6" class="text-danger">${data.message}</td></tr>`;
            return;
        }

        // La API ya devuelve HTML completo del tbody:
        cont.innerHTML = data.html;

        // VOLVER A ENLAZAR BOTONES
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
            abrirAsignacion(btn.dataset.otId, btn.dataset.patente);
        });
    });
}


// ======================================================
//  Enviar asignación (POST)
// ======================================================
document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("formAsignacion");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const ot_id = document.getElementById("asig_ot_id").value;
        const mecanico_rut = document.getElementById("asig_mecanico").value;
        const comentario = document.getElementById("asig_comentario").value.trim();

        if (!comentario) {
            alert("Debe ingresar un comentario.");
            return;
        }

        const fd = new FormData();
        fd.append("ot_id", ot_id);
        fd.append("mecanico_rut", mecanico_rut);
        fd.append("comentario", comentario);

        try {
            const res = await fetch("/api/ordenestrabajo/asignar/", {
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
                alert(data.message || "Error al asignar.");
                return;
            }

            alert("Asignación realizada correctamente.");
            cerrarModal();

            // Recargar tabla sin recargar pantalla
            cargarPendientes();

        } catch (err) {
            console.error(err);
            alert("Error de comunicación con el servidor.");
        }
    });

    // Inicial
    enlazarBotonesAsignar();

    // Auto refresh cada 10s (ajustable)
    setInterval(cargarPendientes, 10000);
});
