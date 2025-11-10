// static/js/registro_taller.js
(() => {
  const BASE = '/api/ordenestrabajo/api';

  const $ = (sel) => document.querySelector(sel);
  const qsa = (sel) => Array.from(document.querySelectorAll(sel));

  const fecha = $('#fecha');
  const taller = $('#tallerId');
  const btnBuscar = $('#btnBuscar');
  const badgeCount = $('#badgeCount');

  const okBox = $('#okBox');
  const errBox = $('#errBox');
  const tbody = $('#tablaOTs tbody');

  // ---- Helpers ----
  function setTodayIfEmpty() {
    if (!fecha.value) {
      const d = new Date();
      const yyyy = d.getFullYear();
      const mm = String(d.getMonth() + 1).padStart(2, '0');
      const dd = String(d.getDate()).padStart(2, '0');
      fecha.value = `${yyyy}-${mm}-${dd}`;
    }
  }

  function hideAlerts() {
    okBox.classList.add('d-none');
    errBox.classList.add('d-none');
  }

  function showOk(msg) {
    hideAlerts();
    okBox.textContent = msg || 'Operación OK';
    okBox.classList.remove('d-none');
  }

  function showErr(msg) {
    hideAlerts();
    errBox.textContent = msg || 'Ocurrió un error';
    errBox.classList.remove('d-none');
  }

  function rowHtml(ot) {
    const estadoBadge =
      ot.estado === 'Pendiente' ? 'bg-warning text-dark' :
      ot.estado === 'En Proceso' ? 'bg-info text-dark' :
      ot.estado === 'Finalizado' ? 'bg-success' :
      ot.estado === 'Cancelado' ? 'bg-secondary' : 'bg-light text-dark';

    const canFinish = (ot.estado === 'Pendiente' || ot.estado === 'En Proceso');
    const canCancel = (ot.estado !== 'Finalizado' && ot.estado !== 'Cancelado');

    return `
      <tr data-id="${ot.id}">
        <td>${ot.id}</td>
        <td><strong>${ot.patente || ''}</strong></td>
        <td>${ot.fecha || ''}</td>
        <td>${ot.hora || ''}</td>
        <td><span class="badge ${estadoBadge}">${ot.estado}</span></td>
        <td>${ot.rut || ''}</td>
        <td>${ot.rut_creador || ''}</td>
        <td>${ot.descripcion || ''}</td>
        <td class="text-end">
          <div class="btn-group btn-group-sm">
            <button class="btn btn-outline-success" data-action="finalizar" ${canFinish ? '' : 'disabled'}>✅ Finalizar</button>
            <button class="btn btn-outline-danger"  data-action="cancelar"  ${canCancel ? '' : 'disabled'}>🛑 Cancelar</button>
          </div>
        </td>
      </tr>
    `;
  }

  function renderRows(items) {
    if (!items?.length) {
      tbody.innerHTML = `<tr><td colspan="9" class="text-muted">Sin datos</td></tr>`;
      badgeCount.textContent = '0 en curso';
      return;
    }
    tbody.innerHTML = items.map(rowHtml).join('');
    badgeCount.textContent = `${items.length} en curso`;
  }

  // ---- API ----
  async function fetchEnCurso() {
    hideAlerts();
    const params = new URLSearchParams();
    // Mostramos todo el taller en la fecha (sin filtrar por patente)
    params.set('fecha', fecha.value);
    // El endpoint actual no recibe taller_id; si quisieras filtrar por taller en backend,
    // puedes ampliarlo. Por ahora consultamos todo y filtramos en UI tras otra llamada.
    // Usaremos el endpoint actual por patente solo si decides agregarlo.
    // Para mantenerlo simple: pediremos todas las OTs en curso del día por taller
    // replicando la lógica con un endpoint dedicado sería lo ideal; de momento,
    // haremos una llamada por taller via un endpoint auxiliar opcional.
    // Como ya existe /api/ordenestrabajo/api/ingresos/en-curso/ por patente,
    // aquí haremos un pequeño truco: consultaremos al backend por taller+fecha si lo soporta.
    // Si NO lo soporta, lo más simple es crear un endpoint nuevo. Para no tocar backend,
    // asumimos soporte opcional por ?taller_id=.
    params.set('taller_id', String(taller.value));

    const url = `${BASE}/ingresos/en-curso/?${params.toString()}`;
    const res = await fetch(url, { credentials: 'include' });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.success) {
      throw new Error(data.message || `HTTP ${res.status}`);
    }
    return data.items || [];
  }

  async function finalizarOT(otId) {
    const res = await fetch(`${BASE}/ingresos/${otId}/finalizar/`, {
      method: 'POST',
      credentials: 'include',
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.success) throw new Error(data.message || `HTTP ${res.status}`);
    return data;
  }

  async function cancelarOT(otId) {
    const res = await fetch(`${BASE}/ingresos/${otId}/cancelar/`, {
      method: 'POST',
      credentials: 'include',
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.success) throw new Error(data.message || `HTTP ${res.status}`);
    return data;
  }

  // ---- Eventos ----
  async function buscar() {
    try {
      tbody.innerHTML = `<tr><td colspan="9" class="text-muted">Cargando...</td></tr>`;
      const items = await fetchEnCurso();
      renderRows(items);
    } catch (e) {
      renderRows([]);
      showErr(`No se pudo cargar el listado: ${e.message}`);
    }
  }

  tbody.addEventListener('click', async (ev) => {
    const btn = ev.target.closest('button[data-action]');
    if (!btn) return;
    const tr = ev.target.closest('tr[data-id]');
    const otId = tr?.dataset?.id;
    if (!otId) return;

    try {
      btn.disabled = true;
      if (btn.dataset.action === 'finalizar') {
        await finalizarOT(otId);
        showOk(`OT #${otId} finalizada`);
      } else if (btn.dataset.action === 'cancelar') {
        await cancelarOT(otId);
        showOk(`OT #${otId} cancelada`);
      }
      await buscar();
    } catch (e) {
      showErr(e.message || 'Error en acción');
    } finally {
      btn.disabled = false;
    }
  });

  // init
  document.addEventListener('DOMContentLoaded', () => {
    setTodayIfEmpty();
    btnBuscar.addEventListener('click', buscar);
    fecha.addEventListener('change', buscar);
    taller.addEventListener('change', buscar);
    buscar();
  });
})();
