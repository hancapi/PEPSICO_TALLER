let fechasOcupadas = {};
let selectedDate = null;
let selectedTime = null;
let currentDate = new Date();

document.addEventListener('DOMContentLoaded', function () {

  // ==============================
  // Funciones de alertas
  // ==============================
  function mostrarExito(mensaje) {
    document.getElementById('successAlert').textContent = mensaje;
    document.getElementById('successAlert').classList.remove('d-none');
    document.getElementById('errorAlert').classList.add('d-none');
  }

  function mostrarError(mensaje) {
    document.getElementById('errorAlert').textContent = mensaje;
    document.getElementById('errorAlert').classList.remove('d-none');
    document.getElementById('successAlert').classList.add('d-none');
  }

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // ==============================
  // Registro de nuevo chofer
  // ==============================
  const registrarBtn = document.getElementById('registrarChoferBtn');
  if (registrarBtn) {
    registrarBtn.addEventListener('click', async () => {
      const nuevoChofer = {
        rut: document.getElementById('rut').value.trim(),
        nombre: document.getElementById('nombreChofer').value.trim(),
        cargo: document.getElementById('cargoChofer').value.trim(),
        region: document.getElementById('regionChofer').value.trim(),
        horario: document.getElementById('horarioChofer').value.trim(),
        disponibilidad: document.getElementById('disponibleChofer').checked ? 1 : 0,
        usuario: document.getElementById('usuarioChofer').value.trim(),
        password: document.getElementById('passwordChofer').value.trim() || "changeme123"
      };

      // Validación de campos obligatorios
      if (!nuevoChofer.rut || !nuevoChofer.nombre || !nuevoChofer.cargo || !nuevoChofer.usuario) {
        mostrarError("Completa todos los campos obligatorios del chofer.");
        return;
      }

      try {
        const res = await fetch('/api/autenticacion/registrar/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
          },
          body: JSON.stringify(nuevoChofer)
        });

        const data = await res.json();

        if (data.success) {
          mostrarExito("Chofer registrado correctamente. Ahora puedes completar el ingreso.");
          document.getElementById('datosChoferNuevo').style.display = 'none';
        } else {
          mostrarError(data.message || "Error al registrar chofer.");
        }

      } catch (error) {
        console.error("Error al registrar chofer:", error);
        mostrarError("Error de conexión al registrar chofer.");
      }
    });
  }

  // ==============================
  // Verificación de RUT existente
  // ==============================
  const rutInput = document.getElementById('rut');
  if (rutInput) {
    rutInput.addEventListener('blur', async function () {
      const rut = this.value.trim();
      if (!rut) return;

      try {
        const res = await fetch(`/api/autenticacion/existe/?rut=${rut}`);
        const data = await res.json();
        document.getElementById('datosChoferNuevo').style.display = data.existe ? 'none' : 'block';
      } catch (err) {
        console.error("Error al verificar RUT:", err);
      }
    });
  }

  // ==============================
  // Verificación de patente de vehículo
  // ==============================
  const patenteInput = document.getElementById('patente');
  if (patenteInput) {
    patenteInput.addEventListener('blur', async function () {
      const patente = this.value.trim();
      if (!patente) return;

      try {
        const res = await fetch(`/vehiculos/existe/?patente=${patente}`);
        const data = await res.json();
        document.getElementById('datosVehiculoNuevo').style.display = !data.existe ? 'block' : 'none';
      } catch (err) {
        console.error("Error al verificar patente:", err);
      }
    });
  }

  // ==============================
  // Cargar horarios ocupados y generar calendario
  // ==============================
  async function cargarHorarios() {
    try {
      const res = await fetch('/api/ordenestrabajo/horarios/');
      const data = await res.json();
      fechasOcupadas = data;
      generateCalendar();
      updateTimeSlots();
    } catch (err) {
      console.error("Error al cargar horarios:", err);
    }
  }
  cargarHorarios();

  // ==============================
  // Formulario de ingreso de vehículo
  // ==============================
  const form = document.getElementById('ingresoForm');
  if (form) {
    form.addEventListener('submit', async function (e) {
      e.preventDefault();

      const data = {
        nombre_chofer: document.getElementById('nombreChofer')?.value.trim(),
        cargo_chofer: document.getElementById('cargoChofer')?.value.trim(),
        region_chofer: document.getElementById('regionChofer')?.value.trim(),
        horario_chofer: document.getElementById('horarioChofer')?.value.trim(),
        disponibilidad_chofer: document.getElementById('disponibleChofer')?.checked,
        usuario_chofer: document.getElementById('usuarioChofer')?.value.trim(),
        patente: document.getElementById('patente')?.value.trim(),
        fecha: document.getElementById('fechaSeleccionada')?.value.trim(),
        hora: document.getElementById('horaSeleccionada')?.value.trim(),
        rut: document.getElementById('rut')?.value.trim(),
        tipo_mantenimiento: document.getElementById('tipoMantenimiento')?.value,
        kilometraje: document.getElementById('kilometraje')?.value,
        descripcion: document.getElementById('descripcion')?.value
      };

      // Validaciones
      const patenteRegex = /^[A-Z]{2,3}\d{2,3}$/i;
      const rutRegex = /^\d{1,2}(\.\d{3}){2}-[\dkK]$|^\d{7,8}-[\dkK]$/;

      if (!patenteRegex.test(data.patente)) {
        mostrarError("Formato de patente inválido (ej: AB1234 o ABC12).");
        return;
      }
      if (!rutRegex.test(data.rut)) {
        mostrarError("Formato de RUT inválido (ej: 12.345.678-9 o 12345678-9).");
        return;
      }
      if (!data.fecha || !data.hora) {
        mostrarError("Debes seleccionar una fecha y hora disponibles.");
        return;
      }

      // Si el vehículo es nuevo, validar datos adicionales
      if (document.getElementById('datosVehiculoNuevo').style.display === 'block') {
        data.marca = document.getElementById('marca').value.trim();
        data.modelo = document.getElementById('modelo').value.trim();
        data.anio = document.getElementById('anio').value.trim();
        data.tipo_vehiculo = document.getElementById('tipo').value.trim();
        data.ubicacion = document.getElementById('ubicacion').value;
        if (!data.ubicacion) {
          mostrarError("Debes seleccionar una ubicación/taller.");
          return;
        }
        if (!data.marca || !data.modelo || !data.anio || !data.tipo_vehiculo || !data.ubicacion) {
          mostrarError("Completa todos los datos del vehículo nuevo.");
          return;
        }
      }

      try {
        const res = await fetch("/api/ordenestrabajo/registrar/", {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
          },
          body: JSON.stringify(data)
        });
        const response = await res.json();

        if (response.status === "nuevo_chofer") {
          mostrarError(response.message);
          document.getElementById('datosChoferNuevo').style.display = 'block';
        } else if (response.status === "ok") {
          mostrarExito(response.message);
          form.reset();
          document.getElementById('datosVehiculoNuevo').style.display = 'none';
          if (!fechasOcupadas[data.fecha]) fechasOcupadas[data.fecha] = [];
          fechasOcupadas[data.fecha].push(data.hora);
          selectedDate = null;
          selectedTime = null;
          generateCalendar();
          updateTimeSlots();
          document.getElementById('scheduleSummary').style.display = 'none';
        } else if (response.status === "redirect") {
          mostrarError(response.message);
          setTimeout(() => { window.location.href = response.redirect_url; }, 2500);
        } else {
          mostrarError(response.message || "Error al registrar");
        }
      } catch (err) {
        console.error("Error en el fetch:", err);
        mostrarError("Error de conexión con el servidor.");
      }
    });
  }

  // ==============================
  // Funciones de calendario y horarios
  // ==============================
  function generateCalendar() {
    const calendar = document.getElementById('calendar');
    if (!calendar) return;
    calendar.innerHTML = '';

    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    document.getElementById('currentMonth').textContent =
      currentDate.toLocaleString('default', { month: 'long', year: 'numeric' });

    for (let i = 0; i < firstDay; i++) {
      const emptyCell = document.createElement('div');
      emptyCell.classList.add('calendar-day', 'empty');
      calendar.appendChild(emptyCell);
    }

    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month, day);
      const dateStr = date.toISOString().split('T')[0];

      const dayCell = document.createElement('div');
      dayCell.classList.add('calendar-day');
      dayCell.textContent = day;

      if (fechasOcupadas[dateStr]) dayCell.classList.add('ocupado');

      dayCell.addEventListener('click', () => selectDate(dateStr));
      calendar.appendChild(dayCell);
    }
  }

  function previousMonth() {
    currentDate.setMonth(currentDate.getMonth() - 1);
    generateCalendar();
    updateTimeSlots();
  }

  function nextMonth() {
    currentDate.setMonth(currentDate.getMonth() + 1);
    generateCalendar();
    updateTimeSlots();
  }

  function selectDate(dateStr) {
    selectedDate = dateStr;
    document.getElementById('fechaSeleccionada').value = dateStr;
    updateTimeSlots();
  }

  function updateTimeSlots() {
    const timeSlots = document.getElementById('timeSlots');
    if (!timeSlots) return;
    timeSlots.innerHTML = '';
    if (!selectedDate) return;

    const horas = ['08:00', '09:00', '10:00', '11:00', '12:00', '14:00', '15:00', '16:00'];
    const ocupadas = fechasOcupadas[selectedDate] || [];

    horas.forEach(hora => {
      const slot = document.createElement('button');
      slot.classList.add('btn', 'btn-outline-primary', 'm-1');
      slot.textContent = hora;
      if (ocupadas.includes(hora)) {
        slot.disabled = true;
        slot.classList.add('btn-secondary');
      }
      slot.addEventListener('click', () => {
        selectedTime = hora;
        document.getElementById('horaSeleccionada').value = hora;
        document.getElementById('selectedSchedule').textContent = `${selectedDate} a las ${hora}`;
        document.getElementById('scheduleSummary').style.display = 'block';
      });
      timeSlots.appendChild(slot);
    });
  }
});
