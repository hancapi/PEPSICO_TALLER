// static/js/ingreso_vehiculo.js
(() => {
  // Seguimos usando el mismo prefijo de API para no romper rutas existentes.
  const API_BASE = "/api/ordenestrabajo";

  const $  = (id)  => document.getElementById(id);

  const form         = $("formIngreso");
  const inputPatente = $("patente");
  const inputFecha   = $("fecha");
  const selectTaller = $("tallerId");
  const inputDesc    = $("descripcion");
  const btnCrear     = $("btnCrear");

  const okIngreso  = $("okIngreso");
  const errIngreso = $("errIngreso");

  // ==========================
  // Helpers
  // ==========================
  function normalizePatente(value) {
    if (!value) return "";
    return value
      .toUpperCase()
      .replace(/\s+/g, "")      // quita espacios
      .replace(/[.\-]/g, "");   // quita puntos y guiones
  }

  function limpiarMensajes() {
    okIngreso?.classList.add("d-none");
    errIngreso?.classList.add("d-none");
  }

  function showOk(msg) {
    limpiarMensajes();
    if (!okIngreso) return;
    okIngreso.textContent = msg;
    okIngreso.classList.remove("d-none");
  }

  function showErr(msg) {
    limpiarMensajes();
    if (!errIngreso) return;
    errIngreso.textContent = msg;
    errIngreso.classList.remove("d-none");
  }

  // ==========================
  // Estado del botón
  // ==========================
  function setButtonLoading(on) {
    if (!btnCrear) return;
    btnCrear.disabled = on;
    btnCrear.innerHTML = on ? "⏳ Enviando..." : "📨 Enviar Solicitud";
  }

  function formReady() {
    if (!btnCrear) return;

    btnCrear.disabled = !(
      inputPatente?.value.trim() &&
      inputFecha?.value &&
      selectTaller?.value
    );
  }

  // ==========================
  // Enviar SOLICITUD de ingreso (solo día)
  // ==========================
  async function crearSolicitud(e) {
    e.preventDefault();

    let patente = inputPatente?.value || "";
    const fecha   = inputFecha?.value;
    const taller  = selectTaller?.value;
    const desc    = inputDesc?.value.trim();

    patente = normalizePatente(patente);

    if (!patente) return showErr("Debe ingresar la patente.");
    if (!fecha)   return showErr("Debe seleccionar una fecha.");
    if (!taller)  return showErr("Debe seleccionar un taller.");

    const fd = new FormData();
    fd.append("patente", patente);
    fd.append("fecha", fecha);
    fd.append("taller_id", taller);
    if (desc) fd.append("descripcion", desc);

    setButtonLoading(true);

    try {
      // La vista /ingresos/create/ interpreta esto como
      // "crear solicitud de ingreso" SIN hora específica.
      const res = await fetch(`${API_BASE}/ingresos/create/`, {
        method: "POST",
        body: fd,
        credentials: "same-origin",
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        return showErr(
          data.message || "No se pudo registrar la solicitud de ingreso."
        );
      }

      showOk(
        data.message || "Solicitud de ingreso registrada correctamente."
      );

      form?.reset();
      // volver a setear fecha por defecto después del reset
      if (inputFecha && !inputFecha.value) {
        const d = new Date();
        inputFecha.value = d.toISOString().slice(0, 10);
      }
      formReady(); // deshabilita el botón hasta que se llenen campos

    } catch (e) {
      console.error("Error creando solicitud de ingreso:", e);
      showErr("Error de comunicación con el servidor.");
    } finally {
      setButtonLoading(false);
    }
  }

  // ==========================
  // Bind inicial
  // ==========================
  function bind() {
    if (!form) return;

    form.addEventListener("submit", crearSolicitud);

    inputPatente?.addEventListener("input", formReady);
    inputFecha?.addEventListener("change", formReady);
    selectTaller?.addEventListener("change", formReady);

    // Setear fecha actual por defecto si viene vacía
    if (inputFecha && !inputFecha.value) {
      const d = new Date();
      inputFecha.value = d.toISOString().slice(0, 10);
    }

    formReady();
  }

  document.readyState === "loading"
    ? document.addEventListener("DOMContentLoaded", bind)
    : bind();
})();
