(function () {
  const $  = (sel) => document.querySelector(sel);

  // Helpers fechas
  function fmt(d) {
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
  }
  function defaultRange() {
    const to = new Date();
    const from = new Date();
    from.setDate(to.getDate() - 7);
    return { from: fmt(from), to: fmt(to) };
  }

  function getRangeOrDefaults() {
    const inFrom = $('#fromDate');
    const inTo   = $('#toDate');
    const haveFrom = inFrom && inFrom.value;
    const haveTo   = inTo   && inTo.value;
    if (haveFrom && haveTo) return { from: inFrom.value, to: inTo.value };
    const def = defaultRange();
    if (inFrom && !inFrom.value) inFrom.value = def.from;
    if (inTo   && !inTo.value)   inTo.value   = def.to;
    return def;
  }

  function getTableFilters() {
    const patente  = ($('#fltPatente')?.value || '').trim().toUpperCase();
    const estado   = ($('#fltEstado')?.value  || '').trim();
    const tallerId = ($('#fltTaller')?.value  || '').trim();
    const creador  = ($('#fltCreador')?.value || '').trim();
    return { patente, estado, taller_id: tallerId, rut_creador: creador };
  }

  function toQuery(params) {
    const usp = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && String(v).trim() !== '') {
        usp.set(k, v);
      }
    });
    return usp.toString();
  }

  async function loadSummary() {
    const { from, to } = getRangeOrDefaults();
    const url = `/reportes/api/summary/?${toQuery({ from, to })}`;
    const res = await fetch(url, { credentials: 'include' });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.success) return;
    $('#statVehiculos') && ($('#statVehiculos').textContent = data.kpis.vehiculos_totales ?? 0);
    $('#statTaller')    && ($('#statTaller').textContent    = data.kpis.en_taller ?? 0);
    $('#statProceso')   && ($('#statProceso').textContent   = data.kpis.en_proceso ?? 0);
    $('#statEmpleados') && ($('#statEmpleados').textContent = data.kpis.empleados_activos ?? 0);
  }

  async function loadOTs() {
    const body = $('#tablaOtsBody');
    if (body) body.innerHTML = '<tr><td colspan="6" class="text-muted">Cargando…</td></tr>';
    $('#tablaCount') && ($('#tablaCount').textContent = '');

    const { from, to } = getRangeOrDefaults();
    const filters = getTableFilters();
    const url = `/reportes/api/ots/?${toQuery({ from, to, ...filters })}`;

    try {
      const res = await fetch(url, { credentials: 'include' });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.success) {
        if (body) body.innerHTML = `<tr><td colspan="6" class="text-danger">Error: ${data.message || res.status}</td></tr>`;
        return;
      }

      const items = Array.isArray(data.items) ? data.items : [];
      if (items.length === 0) {
        if (body) body.innerHTML = '<tr><td colspan="6" class="text-muted">Sin registros en el rango / filtros.</td></tr>';
        return;
      }

      if (body) {
        body.innerHTML = items.map(row => `
          <tr>
            <td>${row.id}</td>
            <td>${row.fecha} ${row.hora || ''}</td>
            <td>${row.patente}</td>
            <td>${row.taller_nombre}</td>
            <td>${row.estado}</td>
            <td>${row.rut_creador || ''}</td>
          </tr>
        `).join('');
      }
      $('#tablaCount') && ($('#tablaCount').textContent = `${items.length} registro(s)`);
    } catch {
      if (body) body.innerHTML = '<tr><td colspan="6" class="text-danger">Error de red</td></tr>';
    }
  }

  function bind() {
    $('#btnConsultar')?.addEventListener('click', (e) => {
      e.preventDefault();
      loadSummary();
      loadOTs();
    });

    $('#btnFiltrar')?.addEventListener('click', (e) => {
      e.preventDefault();
      loadOTs();
    });

    $('#btnLimpiar')?.addEventListener('click', () => {
      $('#fltPatente').value = '';
      $('#fltEstado').value = '';
      $('#fltTaller').value = '';
      $('#fltCreador').value = '';
      loadOTs();
    });

    ['#fltPatente', '#fltTaller', '#fltCreador'].forEach(sel => {
      const el = document.querySelector(sel);
      el && el.addEventListener('keydown', (ev) => {
        if (ev.key === 'Enter') { ev.preventDefault(); loadOTs(); }
      });
    });
    $('#fltEstado')?.addEventListener('change', () => loadOTs());

    const def = defaultRange();
    if (!$('#fromDate').value) $('#fromDate').value = def.from;
    if (!$('#toDate').value)   $('#toDate').value   = def.to;

    loadSummary();
    loadOTs();
  }

  document.addEventListener('DOMContentLoaded', bind);
})();
