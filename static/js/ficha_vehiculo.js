(function () {
  const $ = (sel) => document.querySelector(sel);

  // ===== Helpers fechas
  const fmt = (d) => {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  };
  const setDefaultRange = () => {
    const to = new Date();
    const from = new Date();
    from.setDate(to.getDate() - 30);
    if (!$('#fromDate').value) $('#fromDate').value = fmt(from);
    if (!$('#toDate').value)   $('#toDate').value   = fmt(to);
  };

  // ===== Cargar ficha básica
  async function loadFicha(patente) {
    if (!patente) return;

    const url = `/vehiculos/api/ficha/?patente=${encodeURIComponent(patente)}`;
    const res = await fetch(url, { credentials: 'include' });
    const data = await res.json().catch(() => ({}));

    const notFound = $('#vehiculoNoEncontrado');
    const info = $('#vehiculoInfo');
    const otCard = $('#otActualCard');

    if (!res.ok || !data.success) {
      notFound.classList.remove('d-none');
      info.style.display = 'none';
      otCard.style.display = 'none';
      return;
    }

    if (!data.vehiculo) {
      notFound.classList.remove('d-none');
      info.style.display = 'none';
      otCard.style.display = 'none';
      return;
    }
    notFound.classList.add('d-none');
    info.style.display = '';

    const v = data.vehiculo;
    $('#v_patente').textContent = v.patente || '—';
    $('#v_marca_modelo').textContent = `${v.marca || '—'} ${v.modelo || ''}`.trim();
    $('#v_anio').textContent = v.anio || '—';
    $('#v_tipo').textContent = v.tipo || '—';
    $('#v_ubicacion').textContent = v.ubicacion || '—';
    $('#v_estado').textContent = v.estado || '—';

    // KPIs
    $('#kpi_ots').textContent = data.kpis?.ots ?? 0;
    $('#kpi_incidentes').textContent = data.kpis?.incidentes ?? 0;
    $('#kpi_prestamos').textContent = data.kpis?.prestamos ?? 0;
    $('#kpi_llave').textContent = data.kpis?.llave ?? '—';

    // OT actual
    const ot = data.ot_actual;
    if (ot) {
      otCard.style.display = '';
      $('#otActualEstado').textContent = ot.estado || '—';
      $('#otActualMeta').textContent = `OT #${ot.id} — ${ot.fecha}${ot.hora ? ' ' + ot.hora : ''} — Taller: ${ot.taller_nombre || ot.taller_id}`;
    } else {
      otCard.style.display = 'none';
    }
  }

  // ===== Historial OTs con filtros
  async function loadHistorial(patente) {
    const from = $('#fromDate').value;
    const to   = $('#toDate').value;
    const estado = $('#fltEstado').value;
    const taller = $('#fltTaller').value;

    const params = new URLSearchParams({ patente, from, to });
    if (estado) params.set('estado', estado);
    if (taller) params.set('taller', taller);

    const body = $('#tablaOtsBody');
    body.innerHTML = '<tr><td colspan="6" class="text-muted">Cargando…</td></tr>';

    const url = `/vehiculos/api/ficha/ots/?${params.toString()}`;
    try {
      const res = await fetch(url, { credentials: 'include' });
      const data = await res.json().catch(() => ({}));

      if (!res.ok || !data.success) {
        body.innerHTML = `<tr><td colspan="6" class="text-danger">Error: ${data.message || res.status}</td></tr>`;
        return;
      }

      const items = Array.isArray(data.items) ? data.items : [];
      if (items.length === 0) {
        body.innerHTML = '<tr><td colspan="6" class="text-muted">Sin registros.</td></tr>';
        $('#tablaCount').textContent = '';
        return;
      }

      body.innerHTML = items.map(r => `
        <tr>
          <td>${r.id}</td>
          <td>${r.fecha} ${r.hora || ''}</td>
          <td>${r.taller_nombre || r.taller_id}</td>
          <td>${r.estado}</td>
          <td>${r.rut || ''}</td>
          <td>${r.rut_creador || ''}</td>
        </tr>
      `).join('');

      $('#tablaCount').textContent = `${items.length} registro(s)`;
    } catch {
      body.innerHTML = '<tr><td colspan="6" class="text-danger">Error de red.</td></tr>';
    }
  }

  // ===== Eventos
  function bind() {
    setDefaultRange();

    // Buscar por patente
    $('#formBuscar').addEventListener('submit', (e) => {
      e.preventDefault();
      const p = ($('#patenteInput').value || '').trim().toUpperCase();
      if (!p) return;
      history.replaceState(null, '', `/vehiculos/ficha/?patente=${encodeURIComponent(p)}`);
      loadFicha(p);
      loadHistorial(p);
    });

    // Filtros historial
    $('#btnFiltrar').addEventListener('click', (e) => {
      e.preventDefault();
      const p = ($('#patenteInput').value || '').trim().toUpperCase();
      if (p) loadHistorial(p);
    });
    $('#btnLimpiar').addEventListener('click', () => {
      $('#fltEstado').value = '';
      $('#fltTaller').value = '';
      const p = ($('#patenteInput').value || '').trim().toUpperCase();
      if (p) loadHistorial(p);
    });

    // Carga inicial (si vino “patente” desde la URL/render)
    const p0 = ($('#patenteInput').value || '').trim().toUpperCase();
    if (p0) {
      loadFicha(p0);
      loadHistorial(p0);
    }
  }

  document.addEventListener('DOMContentLoaded', bind);
})();
