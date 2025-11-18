// static/js/ficha_vehiculo.js
(function () {
    const $ = (sel) => document.querySelector(sel);

    // =====================================================
    // CSRF
    // =====================================================
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

    const inputPatente = $('#inputPatente');
    const btnBuscar = $('#btnBuscar');

    const alertBox = $('#alertBox');
    const infoBox = $('#infoVehiculo');

    // Campos vehículo
    const v_patente = $('#v_patente');
    const v_marca = $('#v_marca');
    const v_modelo = $('#v_modelo');
    const v_anio = $('#v_anio');
    const v_tipo = $('#v_tipo');
    const v_ubicacion = $('#v_ubicacion');
    const v_estado = $('#v_estado');

    // KPIs
    const k_ots   = $('#k_ots');
    const k_inc   = $('#k_inc');
    const k_pres  = $('#k_pres');
    const k_llave = $('#k_llave');

    // OT actual
    const otCard   = $('#otActualCard');
    const ot_id    = $('#ot_id');
    const ot_estado = $('#ot_estado');
    const ot_fecha  = $('#ot_fecha');
    const ot_taller = $('#ot_taller');

    // Panel cambio estado
    const panelCambio      = $('#panelCambioEstado');
    const estadoNuevo      = $('#estadoNuevo');
    const comentarioEstado = $('#comentarioEstado');
    const estadoMsg        = $('#estadoMsg');
    const btnGuardarEstado = $('#btnGuardarEstado');

    // Historial
    const timeline = $('#timeline');

    function showAlert(type, msg) {
        alertBox.innerHTML = `
            <div class="alert alert-${type}" role="alert">${msg}</div>
        `;
    }

    // =====================================================
    //  Buscar y cargar información del vehículo
    // =====================================================
    async function buscarVehiculo() {
        const patente = (inputPatente.value || '').trim().toUpperCase();
        if (!patente) {
            showAlert('warning', 'Debe ingresar una patente.');
            return;
        }

        showAlert('info', 'Buscando vehículo...');

        try {
            const url = `/vehiculos/api/ficha/?patente=${encodeURIComponent(patente)}`;
            const res = await fetch(url, { credentials: "same-origin" });
            const data = await res.json();

            if (!data.success) {
                showAlert('danger', data.message || 'Error buscando ficha.');
                return;
            }

            if (!data.vehiculo) {
                showAlert('warning', `No existe información del vehículo <strong>${patente}</strong>.`);
                infoBox.classList.add('hidden');
                return;
            }

            infoBox.classList.remove('hidden');
            alertBox.innerHTML = '';

            // Vehículo
            v_patente.textContent   = data.vehiculo.patente;
            v_marca.textContent     = data.vehiculo.marca;
            v_modelo.textContent    = data.vehiculo.modelo;
            v_anio.textContent      = data.vehiculo.anio ?? '—';
            v_tipo.textContent      = data.vehiculo.tipo;
            v_ubicacion.textContent = data.vehiculo.ubicacion;
            v_estado.textContent    = data.vehiculo.estado;

            // KPIs (los extras pueden venir null)
            k_ots.textContent   = data.kpis.ots;
            k_inc.textContent   = data.kpis.incidentes ?? 0;
            k_pres.textContent  = data.kpis.prestamos ?? 0;
            k_llave.textContent = data.kpis.llave ?? 0;

            // OT actual
            if (data.ot_actual) {
                otCard.style.display   = 'block';
                panelCambio.style.display = 'block';

                ot_id.textContent     = data.ot_actual.id;
                ot_estado.textContent = data.ot_actual.estado;
                ot_fecha.textContent  = `${data.ot_actual.fecha} ${data.ot_actual.hora || ""}`;
                ot_taller.textContent = data.ot_actual.taller_nombre;
            } else {
                otCard.style.display   = 'none';
                panelCambio.style.display = 'none';
            }

            await cargarHistorial(patente);

        } catch (error) {
            console.error(error);
            showAlert('danger', 'Error de red. Intente nuevamente.');
        }
    }

    // =====================================================
    // Historial
    // =====================================================
    async function cargarHistorial(patente) {
        const url = `/vehiculos/api/ficha/ots/?patente=${encodeURIComponent(patente)}`;

        try {
            const res = await fetch(url, { credentials: "same-origin" });
            const data = await res.json();

            timeline.innerHTML = '';

            if (!data.items || data.items.length === 0) {
                timeline.innerHTML = `<li class="text-muted">Sin historial disponible.</li>`;
                return;
            }

            data.items.forEach((ot) => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <strong>OT #${ot.id}</strong> — ${ot.estado}<br>
                    <span class="text-muted">${ot.fecha} ${ot.hora || ''}</span><br>
                    <small>Taller: ${ot.taller_nombre || ot.taller_id}</small>
                `;
                timeline.appendChild(li);
            });

        } catch (err) {
            console.error(err);
            timeline.innerHTML = `<li class="text-danger">Error cargando historial.</li>`;
        }
    }

    // =====================================================
    //  GUARDAR CAMBIO DE ESTADO (usa API oficial)
    // =====================================================
    btnGuardarEstado?.addEventListener("click", async () => {
        const nuevo      = estadoNuevo.value;
        const comentario = comentarioEstado.value.trim();
        const patente    = v_patente.textContent.trim();

        if (!nuevo) {
            estadoMsg.innerHTML = `<div class="alert alert-warning">Seleccione un estado.</div>`;
            return;
        }

        if (nuevo === "Finalizado" && comentario === "") {
            estadoMsg.innerHTML = `<div class="alert alert-danger">Comentario obligatorio para finalizar.</div>`;
            return;
        }

        const fd = new FormData();
        fd.append("patente", patente);
        fd.append("estado", nuevo);
        fd.append("comentario", comentario);

        try {
            // 🔁 Antes: POST a /registro-taller/ (vista HTML)
            // Ahora: usamos la API oficial de cambio de estado
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
                estadoMsg.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
                return;
            }

            estadoMsg.innerHTML = `<div class="alert alert-success">Estado actualizado correctamente.</div>`;

            // Recargar ficha
            setTimeout(() => buscarVehiculo(), 800);

        } catch (err) {
            console.error(err);
            estadoMsg.innerHTML = `<div class="alert alert-danger">Error de red.</div>`;
        }
    });

    // EVENTOS
    btnBuscar?.addEventListener('click', buscarVehiculo);
    inputPatente?.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') buscarVehiculo();
    });

    // Si la página viene con patente en el input, cargamos de inmediato
    if (inputPatente && inputPatente.value.trim() !== "") {
        buscarVehiculo();
    }

})();
