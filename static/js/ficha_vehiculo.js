// =====================================================
//  JS FICHA DEL VEHÍCULO — 100% COMPATIBLE
// =====================================================

(function () {
    const $ = (sel) => document.querySelector(sel);

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
    const k_ots = $('#k_ots');
    const k_inc = $('#k_inc');
    const k_pres = $('#k_pres');
    const k_llave = $('#k_llave');

    // OT actual
    const otCard = $('#otActualCard');
    const ot_id = $('#ot_id');
    const ot_estado = $('#ot_estado');
    const ot_fecha = $('#ot_fecha');
    const ot_taller = $('#ot_taller');

    // Historial
    const timeline = $('#timeline');


    // =====================================================
    //  Mostrar alertas
    // =====================================================
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
            // 1) FICHA VEHÍCULO
            const url = `/vehiculos/api/ficha/?patente=${encodeURIComponent(patente)}`;
            const res = await fetch(url);
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

            // Mostrar contenedor
            infoBox.classList.remove('hidden');
            alertBox.innerHTML = '';

            // Setear datos del vehículo
            v_patente.textContent = data.vehiculo.patente;
            v_marca.textContent = data.vehiculo.marca;
            v_modelo.textContent = data.vehiculo.modelo;
            v_anio.textContent = data.vehiculo.anio ?? '—';
            v_tipo.textContent = data.vehiculo.tipo;
            v_ubicacion.textContent = data.vehiculo.ubicacion;
            v_estado.textContent = data.vehiculo.estado;

            // KPIs
            k_ots.textContent = data.kpis.ots;
            k_inc.textContent = data.kpis.incidentes;
            k_pres.textContent = data.kpis.prestamos;
            k_llave.textContent = data.kpis.llave;

            // OT ACTUAL
            if (data.ot_actual) {
                otCard.style.display = 'block';
                ot_id.textContent = data.ot_actual.id;
                ot_estado.textContent = data.ot_actual.estado;
                ot_fecha.textContent = `${data.ot_actual.fecha} ${data.ot_actual.hora || ""}`;
                ot_taller.textContent = data.ot_actual.taller_nombre;
            } else {
                otCard.style.display = 'none';
            }

            // 2) HISTORIAL
            await cargarHistorial(patente);

        } catch (error) {
            console.error(error);
            showAlert('danger', 'Error de red. Intente nuevamente.');
        }
    }


    // =====================================================
    //  Cargar historial de OTs (timeline)
    // =====================================================
    async function cargarHistorial(patente) {
        const url = `/vehiculos/api/ficha/ots/?patente=${encodeURIComponent(patente)}`;

        try {
            const res = await fetch(url);
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
    //  EVENTOS
    // =====================================================
    btnBuscar.addEventListener('click', buscarVehiculo);

    inputPatente.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') buscarVehiculo();
    });

})();
