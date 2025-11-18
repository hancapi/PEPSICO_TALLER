// static/js/ficha_vehiculo.js
(function () {

    const $ = (sel) => document.querySelector(sel);
    const q = (sel) => [...document.querySelectorAll(sel)];

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

    // Inputs
    const inputPatente = $('#inputPatente');
    const btnBuscar = $('#btnBuscar');
    const alertBox = $('#alertBox');
    const infoBox  = $('#infoVehiculo');

    // Vehículo fields
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

    // Cambio de estado
    const panelCambio = $('#panelCambioEstado');
    const estadoNuevo = $('#estadoNuevo');
    const comentarioEstado = $('#comentarioEstado');
    const estadoMsg = $('#estadoMsg');
    const btnGuardarEstado = $('#btnGuardarEstado');

    // Historial
    const timeline = $('#timeline');

    // DOCUMENTOS
    const cardDocumentos = $('#cardDocumentos');
    const listaDocs = $('#listaDocumentos');
    const formUpload = $('#formUploadDoc');
    const docArchivo = $('#docArchivo');
    const docTitulo = $('#docTitulo');
    const docTipo = $('#docTipo');
    const docMsg = $('#docMsg');
    const btnSubir = $('#btnSubirDoc');

    function showAlert(type, msg) {
        alertBox.innerHTML = `<div class="alert alert-${type}">${msg}</div>`;
    }

    // ============================================================
    // BUSCAR VEHÍCULO
    // ============================================================
    async function buscarVehiculo() {
        const patente = (inputPatente.value || '').trim().toUpperCase();
        if (!patente) {
            showAlert('warning', 'Debe ingresar una patente.');
            return;
        }

        showAlert('info', 'Buscando…');

        try {
            const url = `/vehiculos/api/ficha/?patente=${encodeURIComponent(patente)}`;
            const res = await fetch(url, { credentials: "same-origin" });
            const data = await res.json();

            if (!data.success) {
                showAlert('danger', data.message || 'Error buscando ficha');
                return;
            }

            if (!data.vehiculo) {
                infoBox.classList.add('hidden');
                showAlert('warning', `No existe información del vehículo <b>${patente}</b>`);
                return;
            }

            alertBox.innerHTML = "";
            infoBox.classList.remove("hidden");

            v_patente.textContent = data.vehiculo.patente;
            v_marca.textContent = data.vehiculo.marca;
            v_modelo.textContent = data.vehiculo.modelo;
            v_anio.textContent = data.vehiculo.anio ?? '—';
            v_tipo.textContent = data.vehiculo.tipo;
            v_ubicacion.textContent = data.vehiculo.ubicacion;
            v_estado.textContent = data.vehiculo.estado;

            k_ots.textContent = data.kpis.ots;
            k_inc.textContent = data.kpis.incidentes ?? 0;
            k_pres.textContent = data.kpis.prestamos ?? 0;
            k_llave.textContent = data.kpis.llave ?? 0;

            if (data.ot_actual) {
                otCard.style.display = 'block';
                panelCambio.style.display = 'block';
                cardDocumentos.style.display = 'block';

                ot_id.textContent = data.ot_actual.id;
                ot_estado.textContent = data.ot_actual.estado;
                ot_fecha.textContent = `${data.ot_actual.fecha} ${data.ot_actual.hora || ''}`;
                ot_taller.textContent = data.ot_actual.taller_nombre;

                cargarDocumentos(data.ot_actual.id, patente);

            } else {
                otCard.style.display = 'none';
                panelCambio.style.display = 'none';
                cardDocumentos.style.display = 'none';
            }

            cargarHistorial(patente);

        } catch (err) {
            console.error(err);
            showAlert('danger', 'Error de red.');
        }
    }

    // ============================================================
    // DOCUMENTOS: LISTAR
    // ============================================================
    async function cargarDocumentos(otId, patente) {
        listaDocs.innerHTML = `<li class="list-group-item text-muted">Cargando…</li>`;

        const qsOt = otId ? `ot_id=${otId}` : "";
        const qsPat = patente ? `patente=${patente}` : "";

        const url = `/api/documentos/?${qsOt || qsPat}`;

        try {
            const res = await fetch(url);
            const data = await res.json();

            if (!data.success) {
                listaDocs.innerHTML = `<li class="list-group-item text-danger">${data.message}</li>`;
                return;
            }

            if (!data.documentos.length) {
                listaDocs.innerHTML = `<li class="list-group-item text-muted">Sin documentos.</li>`;
                return;
            }

            listaDocs.innerHTML = "";

            data.documentos.forEach(doc => {
                const li = document.createElement("li");
                li.className = "list-group-item d-flex justify-content-between align-items-center";

                let icon = "📄";
                if (doc.archivo.endsWith(".pdf")) icon = "📕";
                if (doc.archivo.match(/\.(jpg|jpeg|png)$/i)) icon = "🖼️";

                li.innerHTML = `
                    <span>${icon} <b>${doc.titulo}</b>
                        <br><small class="text-muted">${doc.tipo} — ${doc.creado_en}</small>
                    </span>
                    <a href="${doc.archivo}" target="_blank" class="btn btn-sm btn-outline-primary">
                        Abrir
                    </a>
                `;
                listaDocs.appendChild(li);
            });

        } catch (err) {
            console.error(err);
            listaDocs.innerHTML = `<li class="list-group-item text-danger">Error cargando documentos.</li>`;
        }
    }

    // ============================================================
    // DOCUMENTOS: UPLOAD
    // ============================================================
    formUpload?.addEventListener("submit", async e => {
        e.preventDefault();

        const file = docArchivo.files[0];
        const titulo = docTitulo.value.trim();
        const tipo = docTipo.value;
        const otId = ot_id.textContent.trim();
        const patente = v_patente.textContent.trim();

        if (!file) {
            docMsg.innerHTML = `<div class="alert alert-warning">Seleccione un archivo.</div>`;
            return;
        }
        if (!titulo) {
            docMsg.innerHTML = `<div class="alert alert-warning">Debe ingresar un título.</div>`;
            return;
        }

        const fd = new FormData();
        fd.append("archivo", file);
        fd.append("titulo", titulo);
        fd.append("tipo", tipo);
        fd.append("ot_id", otId);
        fd.append("patente", patente);

        try {
            const res = await fetch(`/api/documentos/upload/`, {
                method: "POST",
                body: fd,
                headers: {
                    "X-CSRFToken": csrftoken,
                }
            });

            const data = await res.json();

            if (!data.success) {
                docMsg.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
                return;
            }

            docMsg.innerHTML = `<div class="alert alert-success">Documento subido correctamente.</div>`;

            docArchivo.value = "";
            docTitulo.value = "";

            // recargar lista
            cargarDocumentos(otId, patente);

        } catch (err) {
            console.error(err);
            docMsg.innerHTML = `<div class="alert alert-danger">Error al subir documento.</div>`;
        }
    });

    // ============================================================
    // TIMELINE
    // ============================================================
    async function cargarHistorial(patente) {
        const url = `/vehiculos/api/ficha/ots/?patente=${encodeURIComponent(patente)}`;

        try {
            const res = await fetch(url, { credentials: "same-origin" });
            const data = await res.json();

            timeline.innerHTML = "";

            if (!data.items?.length) {
                timeline.innerHTML = `<li class="text-muted">Sin historial.</li>`;
                return;
            }

            data.items.forEach(ot => {
                const li = document.createElement("li");
                li.innerHTML = `
                    <b>OT #${ot.id}</b> — ${ot.estado}<br>
                    <small class="text-muted">${ot.fecha} ${ot.hora || ""}</small><br>
                    <small>Taller: ${ot.taller_nombre || ot.taller_id}</small>
                `;
                timeline.appendChild(li);
            });

        } catch (err) {
            console.error(err);
            timeline.innerHTML = `<li class="text-danger">Error cargando historial.</li>`;
        }
    }

    // ============================================================
    // EVENTOS
    // ============================================================
    btnBuscar?.addEventListener("click", buscarVehiculo);
    inputPatente?.addEventListener("keyup", e => { if (e.key === "Enter") buscarVehiculo(); });

    // precarga si viene patente en URL
    if (inputPatente && inputPatente.value.trim() !== "") buscarVehiculo();

})();
