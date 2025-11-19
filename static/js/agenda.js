(function () {
    const fechaInput = document.getElementById("inputFecha");
    const btnBuscar = document.getElementById("btnBuscarSlots");
    const slotsContainer = document.getElementById("slotsContainer");

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
        const hora = e.target.dataset.hora;
        const fecha = fechaInput.value;

        const patente = prompt("Ingrese patente del vehículo:");
        if (!patente) return;

        try {
            const fd = new FormData();
            fd.set("patente", patente.toUpperCase());
            fd.set("fecha", fecha);
            fd.set("hora", hora);
            fd.set("taller_id", window.TALLER_ID); // Se injecta desde backend

            const res = await fetch("/ordenestrabajo/api/ingresos/create/", {
                method: "POST",
                body: fd
            });

            const data = await res.json();
            if (!data.success) {
                alert("Error: " + data.message);
                return;
            }

            alert("Ingreso programado correctamente.");
            btnBuscar.click();

        } catch (err) {
            alert("Error de red.");
        }
    }

    btnBuscar.addEventListener("click", async () => {
        const fecha = fechaInput.value;
        if (!fecha) return alert("Seleccione una fecha");

        try {
            const res = await fetch(`/ordenestrabajo/api/agenda/slots/?fecha=${fecha}&taller_id=${window.TALLER_ID}`);
            const data = await res.json();

            if (!data.success) {
                alert("Error: " + data.message);
                return;
            }

            showSlots(data.slots);
        } catch (err) {
            alert("Error al cargar horarios");
        }
    });
})();
