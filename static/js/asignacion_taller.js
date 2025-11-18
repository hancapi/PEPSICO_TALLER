// ======================================================
//  Asignación de Vehículos a Mecánico — Taller PepsiCo
// ======================================================

// -------------------------------
//  Obtener token CSRF (seguro)
// -------------------------------
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let c of cookies) {
            const cookie = c.trim();
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie("csrftoken");


// ======================================================
//  Abrir y cerrar modal
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
//  Enviar asignación al backend
// ======================================================
document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("formAsignacion");

    if (!form) {
        console.error("❌ No existe <form id='formAsignacion'> en el DOM.");
        return;
    }

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

            if (!res.ok) {
                console.error("❌ Error HTTP:", res.status);
                alert("Error al asignar OT.");
                return;
            }

            const data = await res.json();

            if (!data.success) {
                alert(data.message || "Error en la asignación.");
                return;
            }

            alert("Asignación realizada correctamente.");
            cerrarModal();
            location.reload();

        } catch (err) {
            console.error("❌ Error en comunicación:", err);
            alert("Error de comunicación con el servidor.");
        }
    });


    // ======================================================
    //  Enlazar botones con data-attributes
    // ======================================================
    document.querySelectorAll(".btn-asignar").forEach((btn) => {
        btn.addEventListener("click", () => {
            abrirAsignacion(
                btn.dataset.otId,
                btn.dataset.patente
            );
        });
    });

});
