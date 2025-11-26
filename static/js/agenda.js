// static/js/agenda.js
(function () {
    const API_BASE = "/api/ordenestrabajo";

    const fechaInput     = document.getElementById("inputFecha");
    const btnBuscar      = document.getElementById("btnBuscarSlots");
    const slotsContainer = document.getElementById("slotsContainer");

    // ==========================
    // Helpers
    // ==========================
    function normalizePatente(value) {
        if (!value) return "";
        return value
            .toUpperCase()
            .replace(/\s+/g, "")      // quita espacios
            .replace(/[.\-]/g, "");   // quita puntos y guiones
    }

    function showSlots(slots) {
        slotsContainer.innerHTML = "";

        if (!slots.length) {
            slotsContainer.innerHTML = "<p class='text-muted'>Sin horarios.</p>";
            return;
        }

        slots.forEach(slot => {
            const col = document.createElement("div");
            col.className = "col-md-3";

            col.innerHTML = `
                <button class="btn w-100 ${slot.ocupado ? "btn-secondary" : "btn-success"}"
                        ${slot.ocupado ? "disabled" : ""}
                        data-hora="${slot.hora}">
                    ${slot.hora} ${slot.ocupado ? "(Ocupado)" : ""}
                </button>
            `;

            if (!slot.ocupado) {
                col.querySelector("button").addEventListener("click", reservarSlot);
            }

            slotsContainer.appendChild(col);
        });
    }

    async function reservarSlot(e) {
        const hora  = e.target.dataset.hora;
        const fecha = fechaInput.value;

        let patente = prompt("Ingrese patente del vehículo:");
        if (!patente) return;

        patente = normalizePatente(patente);

        if (!patente) {
            alert("Patente inválida.");
            return;
        }

        try {
            const fd = new FormData();
            fd.set("patente", patente);
            fd.set("fecha", fecha);
            fd.set("hora", hora);              // el backend puede ignorarla si no la usa
            fd.set("taller_id", window.TALLER_ID); // se inyecta desde backend

            const res = await fetch(`${API_BASE}/ingresos/create/`, {
                method: "POST",
                body: fd,
                credentials: "same-origin",
            });

            const data = await res.json();
            if (!data.success) {
                alert("Error: " + (data.message || "No se pudo programar el ingreso."));
                return;
            }

            alert(data.message || "Ingreso programado correctamente.");
            btnBuscar.click();

        } catch (err) {
            console.error("Error en reservarSlot:", err);
            alert("Error de red.");
        }
    }

    async function buscarSlots() {
        const fecha = fechaInput.value;
        if (!fecha) {
            alert("Seleccione una fecha");
            return;
        }

        try {
            const res = await fetch(
                `${API_BASE}/agenda/slots/?fecha=${encodeURIComponent(fecha)}&taller_id=${encodeURIComponent(window.TALLER_ID)}`
            );
            const data = await res.json();

            if (!data.success) {
                alert("Error: " + (data.message || "No se pudo cargar los horarios."));
                return;
            }

            showSlots(data.slots);
        } catch (err) {
            console.error("Error al cargar horarios:", err);
            alert("Error al cargar horarios");
        }
    }

    if (btnBuscar) {
        btnBuscar.addEventListener("click", buscarSlots);
    }
})();
