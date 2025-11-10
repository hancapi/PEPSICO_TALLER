// static/js/ingreso_vehiculos.js
(() => {
  const BASE_API = '/api/ordenestrabajo';

  const $  = (id)  => document.getElementById(id);
  const qs = (sel) => document.querySelector(sel);
  const qsa= (sel) => Array.from(document.querySelectorAll(sel));

  const form         = $('formIngreso');
  const btnCrear     = $('btnCrear');
  const okIngreso    = $('okIngreso');
  const errIngreso   = $('errIngreso');

  const inputPatente = $('patente');
  const inputDesc    = $('descripcion');
  const inputFecha   = $('fecha');
  const selectTaller = $('tallerId');

  const slotsGrid    = $('slotsGrid');
  const slotResumen  = $('slotResumen');
  const slotSel      = $('slotSel');

  let horaSeleccionada = null;

  // ===== UI helpers =====
  function clearAlerts() {
    if (okIngreso) { okIngreso.classList.add('d-none'); okIngreso.style.display = 'none'; }
    if (errIngreso){ errIngreso.classList.add('d-none'); errIngreso.style.display = 'none'; }
  }

  function scrollAlertIntoView(el) {
    if (!el) return;
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function showOk(msg) {
    console.debug('[UI] showOk:', msg);
    if (!okIngreso) return;
    okIngreso.textContent = msg || '✅ OT creada correctamente';
    okIngreso.classList.remove('d-none');
    okIngreso.style.display = 'block';
    if (errIngreso) { errIngreso.classList.add('d-none'); errIngreso.style.display = 'none'; }
    scrollAlertIntoView(okIngreso);
  }

  function showErr(msg) {
    console.debug('[UI] showErr:', msg);
    if (!errIngreso) return;
    errIngreso.textContent = `❌ ${msg || 'Error al crear OT'}`;
    errIngreso.classList.remove('d-none');
    errIngreso.style.display = 'block';
    if (okIngreso) { okIngreso.classList.add('d-none'); okIngreso.style.display = 'none'; }
    scrollAlertIntoView(errIngreso);
  }

  function enableCreateButtonIfReady() {
    const patente = inputPatente?.value?.trim();
    const fecha   = inputFecha?.value;
    const taller  = selectTaller?.value;
    const ready   = Boolean(patente && fecha && taller && horaSeleccionada);
    if (btnCrear) btnCrear.disabled = !ready;
  }

  function setSubmitting(on) {
    if (!btnCrear) return;
    if (on) {
      btnCrear.disabled = true;
      btnCrear.innerText = '⏳ Creando...';
    } else {
      btnCrear.innerText = '💾 Crear OT';
      enableCreateButtonIfReady();
    }
  }

  // ===== Agenda =====
  async function cargarAgenda(preserveMsg = false) {
    if (!preserveMsg) clearAlerts();

    horaSeleccionada = null;
    if (slotSel) slotSel.textContent = '';
    if (slotResumen) slotResumen.classList.add('d-none');
    if (btnCrear) btnCrear.disabled = true;

    const fecha    = inputFecha?.value;
    const tallerId = selectTaller?.value;
    if (!fecha || !tallerId) return;

    if (slotsGrid) {
      slotsGrid.innerHTML = '<div class="text-muted">Cargando...</div>';
    }

    try {
      const url = `${BASE_API}/api/agenda/slots/?fecha=${encodeURIComponent(fecha)}&taller_id=${encodeURIComponent(tallerId)}`;
      const res = await fetch(url, { credentials: 'same-origin' });
      const data = await res.json();

      if (!res.ok || !data.success) {
        if (slotsGrid) {
          slotsGrid.innerHTML = `<div class="text-danger">Error cargando agenda: ${data.message || res.status}</div>`;
        }
        return;
      }

      if (!slotsGrid) return;
      const frag = document.createDocumentFragment();

      (data.slots || []).forEach(({ hora, ocupado }) => {
        const b = document.createElement('button');
        b.type = 'button';
        b.className = `btn btn-sm me-2 mb-2 ${ocupado ? 'btn-outline-secondary' : 'btn-outline-success'}`;
        b.textContent = hora;
        b.disabled = !!ocupado;

        b.addEventListener('click', () => {
          qsa('#slotsGrid button').forEach(x => x.classList.remove('active'));
          b.classList.add('active');
          horaSeleccionada = hora;
          if (slotSel) slotSel.textContent = hora;
          if (slotResumen) slotResumen.classList.remove('d-none');
          enableCreateButtonIfReady();
        });

        frag.appendChild(b);
      });

      slotsGrid.innerHTML = '';
      slotsGrid.appendChild(frag);
    } catch (e) {
      console.warn('Error al cargar agenda:', e);
      if (slotsGrid) slotsGrid.innerHTML = `<div class="text-danger">Error de red al cargar agenda</div>`;
    }
  }

  // ===== Crear Ingreso =====
  async function crearIngreso(ev) {
    ev.preventDefault();

    const patente = (inputPatente?.value || '').trim().toUpperCase();
    const fecha   = inputFecha?.value;
    const taller  = selectTaller?.value;
    const hora    = horaSeleccionada;
    const desc    = (inputDesc?.value || '').trim();

    if (!patente) { showErr('Ingresa la patente.'); inputPatente?.focus(); return; }
    if (inputPatente && !inputPatente.checkValidity()) {
      showErr(inputPatente.title || 'Patente inválida.');
      inputPatente.focus();
      return;
    }
    if (!hora)                 { showErr('Selecciona un horario de la agenda.'); return; }
    if (!fecha || !taller)     { showErr('Selecciona fecha y taller.'); return; }

    const formData = new FormData();
    formData.append('patente', patente);
    formData.append('fecha',   fecha);
    formData.append('hora',    hora);
    formData.append('taller_id', String(taller));
    if (desc) formData.append('descripcion', desc);

    try {
      setSubmitting(true);
      const res = await fetch(`${BASE_API}/api/ingresos/create/`, {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
      });

      const isJson = (res.headers.get('content-type') || '').includes('application/json');
      const data = isJson ? await res.json() : null;

      if (!res.ok || !data?.success) {
        const msg = data?.message
          || (res.status === 409 ? 'Conflicto de agenda o vehículo ya en curso.' : `Error HTTP ${res.status}`);
        showErr(msg);
        return;
      }

      const ot = data.ot;
      showOk(`✅ OT #${ot.id} creada: ${ot.patente} a las ${ot.hora} (taller ${ot.taller_id})`);

      await cargarAgenda(true);   // ¡preserva el mensaje!
      if (inputDesc) inputDesc.value = '';
    } catch (e) {
      console.error('crearIngreso error:', e);
      showErr('No se pudo crear la OT. Revisa tu conexión e intenta nuevamente.');
    } finally {
      setSubmitting(false);
    }
  }

  // ===== Bind =====
  function bind() {
    if (form && !form.dataset.bound) {
      form.addEventListener('submit', crearIngreso);
      form.dataset.bound = '1';
    }
    $('btnCargarAgenda')?.addEventListener('click', () => cargarAgenda(false));
    inputFecha?.addEventListener('change',  () => cargarAgenda(false));
    selectTaller?.addEventListener('change',() => cargarAgenda(false));
    inputPatente?.addEventListener('input', enableCreateButtonIfReady);

    if (inputFecha && !inputFecha.value) {
      const d = new Date();
      const yyyy = d.getFullYear();
      const mm = String(d.getMonth() + 1).padStart(2, '0');
      const dd = String(d.getDate()).padStart(2, '0');
      inputFecha.value = `${yyyy}-${mm}-${dd}`;
    }

    cargarAgenda(false);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bind);
  } else {
    bind();
  }
})();
