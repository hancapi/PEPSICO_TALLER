let fechasOcupadas = {};
let selectedDate = null;
let selectedTime = null;
let currentDate = new Date();

document.addEventListener("DOMContentLoaded", async function () {
  console.log("✅ ingreso_vehiculos.js cargado correctamente");

  // Cargar horarios ocupados desde el backend
  await cargarHorariosOcupados();

  // Renderizar calendario inicial
  generarCalendario();

  // Manejar envío de formulario principal
  const form = document.getElementById("ingresoForm");
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    registrarOrdenTrabajo();
  });

  // Manejar cambio de mes
  window.previousMonth = () => cambiarMes(-1);
  window.nextMonth = () => cambiarMes(1);
});

// =============================
// 🔹 Cargar horarios ocupados desde Django
// =============================
async function cargarHorariosOcupados() {
  try {
    const res = await fetch("/api/ordenestrabajo/horarios_ocupados/");
    if (!res.ok) throw new Error(`Error HTTP: ${res.status}`);
    fechasOcupadas = await res.json();
    console.log("📅 Horarios ocupados:", fechasOcupadas);
  } catch (err) {
    console.error("❌ Error al cargar horarios ocupados:", err);
  }
}

// =============================
// 🔹 Generar calendario dinámico
// =============================
function generarCalendario() {
  const calendar = document.getElementById("calendar");
  const currentMonth = document.getElementById("currentMonth");
  calendar.innerHTML = "";

  const mes = currentDate.getMonth();
  const año = currentDate.getFullYear();
  const primerDia = new Date(año, mes, 1);
  const ultimoDia = new Date(año, mes + 1, 0);
  const nombreMes = primerDia.toLocaleString("es-ES", { month: "long" });

  currentMonth.textContent = `${nombreMes.toUpperCase()} ${año}`;

  for (let d = 1; d <= ultimoDia.getDate(); d++) {
    const fecha = new Date(año, mes, d);
    const fechaISO = fecha.toISOString().split("T")[0];

    const btn = document.createElement("button");
    btn.className = "calendar-day btn btn-outline-secondary";
    btn.textContent = d;

    if (fechasOcupadas[fechaISO]) btn.classList.add("ocupado");

    btn.addEventListener("click", () => seleccionarFecha(fechaISO));
    calendar.appendChild(btn);
  }
}

// =============================
// 🔹 Cambiar mes del calendario
// =============================
function cambiarMes(delta) {
  currentDate.setMonth(currentDate.getMonth() + delta);
  generarCalendario();
}

// =============================
// 🔹 Seleccionar fecha y mostrar horarios
// =============================
function seleccionarFecha(fechaISO) {
  selectedDate = fechaISO;
  document.getElementById("fechaSeleccionada").value = fechaISO;

  const timeSlots = document.getElementById("timeSlots");
  timeSlots.innerHTML = "";
  const ocupados = fechasOcupadas[fechaISO] || [];

  const horarios = generarBloquesHorarios();
  horarios.forEach((hora) => {
    const btn = document.createElement("button");
    btn.className = "btn btn-outline-primary m-1";
    btn.textContent = hora;

    if (ocupados.includes(hora)) {
      btn.disabled = true;
      btn.classList.add("btn-danger");
    }

    btn.addEventListener("click", () => seleccionarHora(hora));
    timeSlots.appendChild(btn);
  });
}

// =============================
// 🔹 Generar bloques horarios
// =============================
function generarBloquesHorarios() {
  const horas = [];
  let h = 9,
    m = 0;
  while (h < 18) {
    const hh = h.toString().padStart(2, "0");
    const mm = m.toString().padStart(2, "0");
    horas.push(`${hh}:${mm}`);
    m += 30;
    if (m === 60) {
      m = 0;
      h++;
    }
  }
  return horas;
}

// =============================
// 🔹 Seleccionar hora
// =============================
function seleccionarHora(hora) {
  selectedTime = hora;
  document.getElementById("horaSeleccionada").value = hora;

  document.querySelectorAll("#timeSlots button").forEach((b) =>
    b.classList.remove("active")
  );
  const btn = [...document.querySelectorAll("#timeSlots button")].find(
    (b) => b.textContent === hora
  );
  if (btn) btn.classList.add("active");

  const summary = document.getElementById("scheduleSummary");
  document.getElementById(
    "selectedSchedule"
  ).textContent = `${selectedDate} a las ${hora}`;
  summary.style.display = "block";
}

// =============================
// 🔹 Registrar orden de trabajo
// =============================
async function registrarOrdenTrabajo() {
  const patente = document.getElementById("patente").value;
  const rut = document.getElementById("rut").value;
  const tipo_mantenimiento = document.getElementById("tipoMantenimiento").value;
  const kilometraje = document.getElementById("kilometraje").value;
  const descripcion = document.getElementById("descripcion").value;
  const marca = document.getElementById("marca").value;
  const modelo = document.getElementById("modelo").value;
  const anio = document.getElementById("anio").value;
  const tipo_vehiculo = document.getElementById("tipo").value;
  const ubicacion = document.getElementById("ubicacion").value;

  if (!selectedDate || !selectedTime) {
    mostrarError("Debes seleccionar una fecha y hora disponibles.");
    return;
  }

  const datos = {
    patente,
    rut,
    tipo_mantenimiento,
    kilometraje,
    descripcion,
    marca,
    modelo,
    anio,
    tipo_vehiculo,
    ubicacion,
    fecha: selectedDate,
    hora: selectedTime,
  };

  try {
    const res = await fetch("/api/ordenestrabajo/registrar/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(datos),
    });

    const data = await res.json();

    if (data.status === "ok") {
      mostrarExito("Orden registrada correctamente.");
      await cargarHorariosOcupados();
      generarCalendario();
    } else {
      mostrarError(data.message || "Error al registrar la orden.");
    }
  } catch (err) {
    console.error("❌ Error:", err);
    mostrarError("No se pudo registrar la orden.");
  }
}

// =============================
// 🔹 Funciones de alerta
// =============================
function mostrarExito(msg) {
  const alert = document.getElementById("successAlert");
  alert.textContent = msg;
  alert.classList.remove("d-none");
  setTimeout(() => alert.classList.add("d-none"), 4000);
}

function mostrarError(msg) {
  const alert = document.getElementById("errorAlert");
  alert.textContent = msg;
  alert.classList.remove("d-none");
  setTimeout(() => alert.classList.add("d-none"), 5000);
}

