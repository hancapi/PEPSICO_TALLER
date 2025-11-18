(() => {
  const API_BASE = "/api/ordenestrabajo";

  const $  = (id) => document.getElementById(id);
  const qsa = (sel) => [...document.querySelectorAll(sel)];

  const form          = $("formIngreso");
  const inputPatente  = $("patente");
  const inputFecha    = $("fecha");
  const selectTaller  = $("tallerId");
  const inputDesc     = $("descripcion");
  const btnCrear      = $("btnCrear");

  const slotsGrid     = $("slotsGrid");
  const slotSel       = $("slotSel");
  const slotResumen   = $("slotResumen");

  const okIngreso     = $("okIngreso");
  const errIngreso    = $("errIngreso");

  const tablaUltimos  = $("tablaUltimosIngresos");

  let horaSeleccionada = null;

  function limpiarMensajes() {
    okIngreso?.classList.add("d-none");
    errIngreso?.classList.add("d-none");
  }

  function showOk(msg) {
    limpiarMensajes();
    okIngreso.textContent = msg;
    okIngreso.classList.remove("d-none");
  }

  function showErr(msg) {
    limpiarMensajes();
    errIngreso.textContent = msg;
    errIngreso.classList.remove("d-none");
  }

  function setButtonLoading(on) {
    btnCrear.disabled = on;
    btnCrear.innerHTML = on ? "⏳ Creando..." : "💾 Crear OT";
  }

  function formReady() {
    btnCrear.disabled = !(
      inputPatente?.value.trim() &&
      inputFecha?.value &&
      selectTaller?.value &&
      horaSeleccionada
    );
  }

  async function cargarAgenda(preserveMsg = false) {
    if (!preserveMsg) limpiarMensajes();

    horaSeleccionada = null;
    slotSel.textContent = "";
    slotResumen.classList.add("d-none");
    btnCrear.disabled = true;

    const fecha  = inputFecha.value;
    const taller = selectTaller.value;

    if (!fecha || !taller) return;

    slotsGrid.innerHTML = `<div class="text-muted">Cargando agenda...</div>`;

    try {
      const url = `${API_BASE}/agenda/slots/?fecha=${encodeURIComponent(fecha)}&taller_id=${encodeURIComponent(taller)}`;
      const res = await fetch(url, { credentials: "same-origin" });
      const data = await res.json();

      if (!data.success) {
        slotsGrid.innerHTML = `<div class="text-danger">${data.message}</div>`;
        return;
      }

      slotsGrid.innerHTML = "";
      data.slots.forEach((slot) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className =
          "btn btn-sm me-2 mb-2 " +
          (slot.ocupado ? "btn-outline-secondary" : "btn-outline-success");
        btn.textContent = slot.hora;
        btn.disabled = slot.ocupado;

        btn.addEventListener("click", () => {
          qsa("#slotsGrid button").forEach((b) => b.classList.remove("active"));
          btn.classList.add("active");

          horaSeleccionada = slot.hora;
          slotSel.textContent = horaSeleccionada;
          slotResumen.classList.remove("d-none");
          formReady();
        });

        slotsGrid.appendChild(btn);
      });
    } catch (e) {
      console.error("Error cargando agenda:", e);
      slotsGrid.innerHTML = `<div class="text-danger">No se pudo cargar la agenda.</div>`;
    }
  }

  async function crearIngreso(e) {
    e.preventDefault();

    const patente = inputPatente.value.trim();
    const fecha   = inputFecha.value;
    const taller  = selectTaller.value;
    const hora    = horaSeleccionada;
    const desc    = inputDesc?.value.trim();

    if (!patente) return showErr("Debe ingresar la patente.");
    if (!fecha) return showErr("Debe seleccionar una fecha.");
    if (!taller) return showErr("Debe seleccionar un taller.");
    if (!hora) return showErr("Debe seleccionar un horario.");

    const fd = new FormData();
    fd.append("patente", patente.toUpperCase());
    fd.append("fecha", fecha);
    fd.append("hora", hora);
    fd.append("taller_id", taller);
    if (desc) fd.append("descripcion", desc);

    setButtonLoading(true);

    try {
      const res = await fetch(`${API_BASE}/ingresos/create/`, {
        method: "POST",
        body: fd,
        credentials: "same-origin",
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        return showErr(data.message || "No se pudo crear la OT.");
      }

      showOk(`OT #${data.ot.id} creada correctamente.`);

      form.reset();
      horaSeleccionada = null;
      slotResumen.classList.add("d-none");
      btnCrear.disabled = true;

      await cargarAgenda(true);
      await cargarUltimosIngresos();

    } catch (e) {
      console.error("Error creando OT:", e);
      showErr("Error de comunicación con el servidor.");
    } finally {
      setButtonLoading(false);
    }
  }

  async function cargarUltimosIngresos() {
    if (!tablaUltimos) return;

    try {
      const res = await fetch(`${API_BASE}/ultimas/?solo_disponibles=1`, {
        credentials: "same-origin",
      });

      const data = await res.json();

      if (data.success) {
        tablaUltimos.innerHTML = data.html;
      }
    } catch (e) {
      console.error("Error cargando últimos ingresos:", e);
    }
  }

  function bind() {
    if (!form) return;

    form.addEventListener("submit", crearIngreso);

    inputPatente.addEventListener("input", formReady);
    inputFecha.addEventListener("change", () => cargarAgenda(false));
    selectTaller.addEventListener("change", () => cargarAgenda(false));

    if (!inputFecha.value) {
      const d = new Date();
      inputFecha.value = d.toISOString().slice(0, 10);
    }

    cargarAgenda(false);
    cargarUltimosIngresos();
  }

  document.readyState === "loading"
    ? document.addEventListener("DOMContentLoaded", bind)
    : bind();
})();
