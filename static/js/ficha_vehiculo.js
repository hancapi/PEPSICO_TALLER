// static/js/ficha_vehiculo.js
(function () {

    const $ = (sel) => document.querySelector(sel);

    // Obtener csrf
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


    // Inputs principales
    const inputPatente = $('#inputPatente');
    const btnBuscar = $('#btnBuscar');
    const alertBox = $('#alertBox');
    const infoBox = $('#infoVehiculo');

    // Campos de vehículo
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

    // Cambio estado
    const panelCambio = $('#panelCambioEstado');
    const estadoNuevo = $('#estadoNuevo');
    const comentarioEstado = $('#comentarioEstado');
    const estadoMsg = $('#estadoMsg');
    const btnGuardarEstado = $('#btnGuardarEstado');

    // Timeline
    const timeline = $('#timeline');

    // Documentos
    const cardDocumentos = $('#cardDocumentos');
    const listaDocs = $('#listaDocumentos');  // ← documentos OT actual
    const formUpload = $('#formUploadDoc');
    const docArchivo = $('#docArchivo');
    const docTitulo = $('#docTitulo');
    const docTipo = $('#docTipo');
    const docMsg = $('#docMsg');

    // NUEVAS SECCIONES
    let listaDocsFinalizadas = null;
    let listaDocsVehiculo = null;


    function showAlert(type, msg) {
        alertBox.innerHTML = `<div class="alert alert-${type}">${msg}</div>`;
    }


// ============================================================
// LIMPIAR FICHA
// ============================================================
function limpiarFicha() {
    // Ocultamos ficha y paneles
    infoBox.classList.add("hidden");
    otCard.style.display = "none";
    panelCambio.style.display = "none";
    cardDocumentos.style.display = "none";

    // Limpiamos campos de vehículo
    v_patente.textContent = "";
    v_marca.textContent = "";
    v_modelo.textContent = "";
    v_anio.textContent = "";
    v_tipo.textContent = "";
    v_ubicacion.textContent = "";
    v_estado.textContent = "";

    // Limpiamos KPIs
    k_ots.textContent = "";
    k_inc.textContent = "";
    k_pres.textContent = "";
    k_llave.textContent = "";

    // Limpiamos historial y documentos
    timeline.innerHTML = "";
    if (listaDocs) listaDocs.innerHTML = "";
    if (listaDocsFinalizadas) listaDocsFinalizadas.innerHTML = "";
    if (listaDocsVehiculo) listaDocsVehiculo.innerHTML = "";
}

// ============================================================
// BUSCAR VEHÍCULO
// ============================================================
async function buscarVehiculo() {
    const patente = (inputPatente.value || "").trim().toUpperCase();

    if (!patente) {
        showAlert("warning", "Debe ingresar una patente.");
        limpiarFicha();
        return;
    }

    showAlert("info", "Buscando…");

    try {
        const url = `/vehiculos/api/ficha/?patente=${encodeURIComponent(patente)}`;
        const res = await fetch(url);
        const data = await res.json();

        if (!data.success) {
            showAlert("danger", data.message);
            return;
        }

        if (!data.vehiculo) {
            limpiarFicha();
            showAlert("warning", `No existe información del vehículo <b>${patente}</b>`);
            return;
        }

        alertBox.innerHTML = "";
        infoBox.classList.remove("hidden");

        // Datos vehículo
        v_patente.textContent = data.vehiculo.patente;
        v_marca.textContent = data.vehiculo.marca;
        v_modelo.textContent = data.vehiculo.modelo;
        v_anio.textContent = data.vehiculo.anio ?? '—';
        v_tipo.textContent = data.vehiculo.tipo;
        v_ubicacion.textContent = data.vehiculo.ubicacion;
        v_estado.textContent = data.vehiculo.estado;

        // KPIs
        k_ots.textContent = data.kpis.ots;
        k_inc.textContent = data.kpis.incidentes ?? 0;
        k_pres.textContent = data.kpis.prestamos ?? 0;
        k_llave.textContent = data.kpis.llave ?? 0;

        // OT actual
        if (data.ot_actual) {
            otCard.style.display = "block";
            panelCambio.style.display = "block";
            cardDocumentos.style.display = "block";

            ot_id.textContent = data.ot_actual.id;
            ot_estado.textContent = data.ot_actual.estado;
            ot_fecha.textContent = `${data.ot_actual.fecha} ${data.ot_actual.hora || ""}`;
            ot_taller.textContent = data.ot_actual.taller_nombre;

            cargarDocumentos(data.ot_actual.id, patente);

        } else {
            otCard.style.display = "none";
            panelCambio.style.display = "none";
            cardDocumentos.style.display = "block";

            ot_id.textContent = "";
            ot_estado.textContent = "";
            ot_fecha.textContent = "";
            ot_taller.textContent = "";

            cargarDocumentos(null, patente);
        }

        cargarHistorial(patente);

    } catch (err) {
        console.error(err);
        showAlert("danger", "Error de red.");
    }
}

// ============================================================
// EVENTO INPUT EN EL BUSCADOR
// ============================================================
inputPatente.addEventListener("input", () => {
    const patente = (inputPatente.value || "").trim();
    if (!patente) {
        limpiarFicha(); // 🔹 sin alerta, solo limpieza
    }
});

    // ============================================================
    // NUEVO FORMATO DOCUMENTOS AGRUPADOS
    // ============================================================
    async function cargarDocumentos(otId, patente) {

        listaDocs.innerHTML = `<li class="list-group-item text-muted">Cargando…</li>`;

        const url = `/api/documentos/?ot_id=${otId || ""}&patente=${patente}`;

        try {
            const res = await fetch(url);
            const data = await res.json();

            if (!data.success) {
                listaDocs.innerHTML = `<li class="list-group-item text-danger">${data.message}</li>`;
                return;
            }

            // -----------------------------------------
            // ADAPTACIÓN A BACKEND NUEVO + ANTIGUO
            // -----------------------------------------
            let docsActual = [];
            let docsFinalizadas = [];
            let docsVehiculo = [];

            if (data.actual || data.finalizadas || data.vehiculo) {
                // Backend nuevo
                docsActual = data.actual || [];
                docsFinalizadas = data.finalizadas || [];
                docsVehiculo = data.vehiculo || [];
            } 
            else if (data.documentos) {
                // Backend antiguo
                const todos = data.documentos;

                docsActual = otId ? todos.filter(d => d.ot_id == otId) : [];
                docsFinalizadas = todos.filter(d => d.ot_id && d.ot_id != otId);
                docsVehiculo = todos.filter(d => !d.ot_id);
            }

            // Limpiar secciones previas
            listaDocs.innerHTML = "";
            if (listaDocsFinalizadas) listaDocsFinalizadas.remove();
            if (listaDocsVehiculo) listaDocsVehiculo.remove();
            listaDocsFinalizadas = null;
            listaDocsVehiculo = null;

            // -----------------------------------------
            // 1) OT ACTUAL
            // -----------------------------------------
            if (docsActual.length) {
                renderListaSimple(listaDocs, docsActual);
            } else {
                listaDocs.innerHTML = `<li class="list-group-item text-muted">Sin documentos de OT actual.</li>`;
            }

            // -----------------------------------------
            // 2) OTs finalizadas
            // -----------------------------------------
            renderDocsFinalizadas(docsFinalizadas);

            // -----------------------------------------
            // 3) Docs del vehículo
            // -----------------------------------------
            renderDocsVehiculo(docsVehiculo);

        } catch (err) {
            console.error(err);
            listaDocs.innerHTML = `<li class="list-group-item text-danger">Error cargando documentos.</li>`;
        }
    }


    // Render simple (solo documentos)
    function renderListaSimple(container, docs) {
        docs.forEach(doc => {
            const li = document.createElement("li");
            li.className = "list-group-item d-flex justify-content-between align-items-center";

            li.innerHTML = `
                <span>
                    <b>${doc.titulo}</b><br>
                    <small class="text-muted">${doc.tipo} — ${doc.creado_en}</small>
                </span>
                <a href="${doc.archivo}" target="_blank" class="btn btn-sm btn-outline-primary">
                    Abrir
                </a>
            `;
            container.appendChild(li);
        });
    }


    // Render OTs finalizadas
    function renderDocsFinalizadas(lista) {

        if (!listaDocsFinalizadas) {
            listaDocsFinalizadas = document.createElement("div");
            listaDocsFinalizadas.className = "mt-4";
            listaDocs.appendChild(listaDocsFinalizadas);
        }

        listaDocsFinalizadas.innerHTML = `<h6 class="fw-bold mt-4">📁 OTs Finalizadas</h6>`;

        if (!lista?.length) {
            listaDocsFinalizadas.innerHTML += `
                <div class="text-muted ms-2">No hay documentos en OTs finalizadas.</div>
            `;
            return;
        }

        lista.forEach(grupo => {
            let html = `
                <div class="border rounded p-2 mb-2">
                    <div class="fw-bold mb-1">OT #${grupo.ot_id} — ${grupo.fecha}</div>
            `;

            grupo.docs.forEach(doc => {
                html += `
                    <div class="d-flex justify-content-between border-bottom py-1">
                        <span>${doc.titulo}</span>
                        <a class="btn btn-sm btn-outline-primary" target="_blank" href="${doc.archivo}">
                            Abrir
                        </a>
                    </div>
                `;
            });

            html += `</div>`;
            listaDocsFinalizadas.innerHTML += html;
        });
    }


    // Render documentos sueltos del vehículo
    function renderDocsVehiculo(lista) {

        if (!listaDocsVehiculo) {
            listaDocsVehiculo = document.createElement("div");
            listaDocsVehiculo.className = "mt-4";
            listaDocs.appendChild(listaDocsVehiculo);
        }

        listaDocsVehiculo.innerHTML = `<h6 class="fw-bold mt-4">🚗 Documentos del Vehículo</h6>`;

        if (!lista?.length) {
            listaDocsVehiculo.innerHTML += `
                <div class="text-muted ms-2">Sin documentos del vehículo.</div>
            `;
            return;
        }

        lista.forEach(doc => {
            listaDocsVehiculo.innerHTML += `
                <div class="d-flex justify-content-between border-bottom py-1">
                    <span>${doc.titulo}</span>
                    <a class="btn btn-sm btn-outline-primary" target="_blank" href="${doc.archivo}">
                        Abrir
                    </a>
                </div>
            `;
        });
    }


    // ============================================================
    // SUBIR DOCUMENTO
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
                headers: { "X-CSRFToken": csrftoken }
            });

            const data = await res.json();

            if (!data.success) {
                docMsg.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
                return;
            }

            docMsg.innerHTML = `<div class="alert alert-success">Documento subido correctamente.</div>`;

            docArchivo.value = "";
            docTitulo.value = "";

            cargarDocumentos(otId, patente);

        } catch (err) {
            console.error(err);
            docMsg.innerHTML = `<div class="alert alert-danger">Error al subir documento.</div>`;
        }
    });



    // ============================================================
    // CAMBIO DE ESTADO
    // ============================================================
    async function cambiarEstado() {
        const patente = v_patente.textContent.trim();
        const nuevo = estadoNuevo.value;
        const comentario = comentarioEstado.value.trim();

        estadoMsg.innerHTML = "";

        if (!nuevo) {
            estadoMsg.innerHTML = `<div class="alert alert-warning">Seleccione un estado.</div>`;
            return;
        }

        if (nuevo === "Finalizado" && comentario === "") {
            estadoMsg.innerHTML = `<div class="alert alert-warning">Debe agregar un comentario para finalizar.</div>`;
            return;
        }

        const fd = new FormData();
        fd.append("patente", patente);
        fd.append("estado", nuevo);
        fd.append("comentario", comentario);

        try {
            const res = await fetch("/api/ordenestrabajo/estado/cambiar/", {
                method: "POST",
                body: fd,
                headers: { "X-CSRFToken": csrftoken }
            });

            const data = await res.json();

            if (!data.success) {
                estadoMsg.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
                return;
            }

            estadoMsg.innerHTML = `<div class="alert alert-success">Estado actualizado correctamente.</div>`;

            buscarVehiculo();

        } catch (err) {
            console.error(err);
            estadoMsg.innerHTML = `<div class="alert alert-danger">Error al actualizar estado.</div>`;
        }
    }


    // ============================================================
    // TIMELINE
    // ============================================================
    async function cargarHistorial(patente) {
        const url = `/vehiculos/api/ficha/ots/?patente=${encodeURIComponent(patente)}`;

        try {
            const res = await fetch(url);
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
    btnGuardarEstado?.addEventListener("click", cambiarEstado);
    btnBuscar?.addEventListener("click", buscarVehiculo);
    inputPatente?.addEventListener("keyup", e => {
        if (e.key === "Enter") buscarVehiculo();
    });

    // Precarga si viene con patente
    if (inputPatente && inputPatente.value.trim() !== "") buscarVehiculo();

})();
