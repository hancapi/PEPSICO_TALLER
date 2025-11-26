// static/js/reportes_ot.js
(function () {
  const $ = (sel) => document.querySelector(sel);

  // ============================
  // Helpers fechas
  // ============================
  function fmt(d) {
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd}`;
  }

  function defaultRange() {
    const to = new Date();
    const from = new Date();
    from.setDate(to.getDate() - 7);
    return { from: fmt(from), to: fmt(to) };
  }

  function getRangeOrDefaults() {
    const inFrom = $("#fromDate");
    const inTo = $("#toDate");
    const haveFrom = inFrom && inFrom.value;
    const haveTo = inTo && inTo.value;

    if (haveFrom && haveTo) {
      return { from: inFrom.value, to: inTo.value };
    }

    const def = defaultRange();
    if (inFrom && !inFrom.value) inFrom.value = def.from;
    if (inTo && !inTo.value) inTo.value = def.to;
    return def;
  }

  // ============================
  // Filtros tabla
  // ============================
  function getTableFilters() {
    const patente = ($("#fltPatente")?.value || "").trim().toUpperCase();
    const estado = ($("#fltEstado")?.value || "").trim();
    const tallerId = ($("#fltTaller")?.value || "").trim();
    const creador = ($("#fltCreador")?.value || "").trim();
    return { patente, estado, taller_id: tallerId, rut_creador: creador };
  }

  function toQuery(params) {
    const usp = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && String(v).trim() !== "") {
        usp.set(k, v);
      }
    });
    return usp.toString();
  }

  // ============================
  // Cargar KPIs
  // ============================
  async function loadSummary() {
    const { from, to } = getRangeOrDefaults();
    const url = `/reportes/api/summary/?${toQuery({ from, to })}`;

    try {
      const res = await fetch(url, { credentials: "same-origin" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.success) return;

      const k = data.kpis || {};
      $("#statVehiculos") &&
        ($("#statVehiculos").textContent = k.vehiculos_totales ?? 0);
      $("#statTaller") &&
        ($("#statTaller").textContent = k.en_taller ?? 0);
      $("#statProceso") &&
        ($("#statProceso").textContent = k.en_proceso ?? 0);
      $("#statEmpleados") &&
        ($("#statEmpleados").textContent = k.empleados_activos ?? 0);
    } catch (e) {
      console.error("Error loadSummary", e);
    }
  }

  // ============================
  // Cargar tabla de OTs
  // ============================
  async function loadOTs() {
    const body = $("#tablaOtsBody");
    if (body)
      body.innerHTML =
        '<tr><td colspan="10" class="text-muted">Cargando…</td></tr>';
    $("#tablaCount") && ($("#tablaCount").textContent = "");

    const { from, to } = getRangeOrDefaults();
    const filters = getTableFilters();
    const url = `/reportes/api/ots/?${toQuery({ from, to, ...filters })}`;

    try {
      const res = await fetch(url, { credentials: "same-origin" });
      const data = await res.json().catch(() => ({}));

      if (!res.ok || !data.success) {
        if (body) {
          body.innerHTML = `<tr><td colspan="10" class="text-danger">Error: ${
            data.message || res.status
          }</td></tr>`;
        }
        return;
      }

      const items = Array.isArray(data.items) ? data.items : [];
      if (items.length === 0) {
        if (body) {
          body.innerHTML =
            '<tr><td colspan="10" class="text-muted">Sin registros en el rango / filtros.</td></tr>';
        }
        return;
      }

      if (body) {
        body.innerHTML = items
          .map(
            (row) => `
          <tr>
            <td>${row.id}</td>
            <td>${row.fecha} ${row.hora || ""}</td>
            <td>${row.patente}</td>
            <td>${row.vehiculo || ""}</td>
            <td>${row.taller_nombre || ""}</td>
            <td>${row.estado}</td>
            <td>${row.rut_mecanico || ""}</td>
            <td>${row.rut_creador || ""}</td>
            <td>${row.fecha_salida || ""}</td>
            <td>${row.duracion_dias ?? ""}</td>
          </tr>
        `
          )
          .join("");
      }

      $("#tablaCount") &&
        ($("#tablaCount").textContent = `${items.length} registro(s)`);
    } catch (e) {
      console.error("Error loadOTs", e);
      if (body) {
        body.innerHTML =
          '<tr><td colspan="10" class="text-danger">Error de red</td></tr>';
      }
    }
  }

  // ============================
  // Bind de eventos
  // ============================
  function bind() {
    $("#btnConsultar")?.addEventListener("click", (e) => {
      e.preventDefault();
      loadSummary();
      loadOTs();
    });

    $("#btnFiltrar")?.addEventListener("click", (e) => {
      e.preventDefault();
      loadOTs();
    });

    $("#btnLimpiar")?.addEventListener("click", () => {
      const patente = $("#fltPatente");
      const estado = $("#fltEstado");
      const taller = $("#fltTaller");
      const creador = $("#fltCreador");
      patente && (patente.value = "");
      estado && (estado.value = "");
      taller && (taller.value = "");
      creador && (creador.value = "");
      loadOTs();
    });

    ["#fltPatente", "#fltTaller", "#fltCreador"].forEach((sel) => {
      const el = document.querySelector(sel);
      el &&
        el.addEventListener("keydown", (ev) => {
          if (ev.key === "Enter") {
            ev.preventDefault();
            loadOTs();
          }
        });
    });

    $("#fltEstado")?.addEventListener("change", () => loadOTs());

    // Rango por defecto (protegido por null-check)
    const def = defaultRange();
    const fromInput = $("#fromDate");
    const toInput = $("#toDate");
    if (fromInput && !fromInput.value) fromInput.value = def.from;
    if (toInput && !toInput.value) toInput.value = def.to;

    // Carga inicial
    loadSummary();
    loadOTs();
  }

  document.addEventListener("DOMContentLoaded", bind);
})();
