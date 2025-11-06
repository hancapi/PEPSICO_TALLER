// static/js/ingreso_vehiculos.js
let fechasOcupadas = {};
let selectedDate = null;
let selectedTime = null;
let currentDate = new Date();

// ==============================
// Funciones globales para el calendario
// ==============================
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

document.addEventListener('DOMContentLoaded', function () {

    // ==============================
    // Funciones de alertas
    // ==============================
    function mostrarExito(mensaje) {
        console.log("✅ MOSTRAR ÉXITO:", mensaje);
        const alerta = document.getElementById('successAlert');
        const errorAlerta = document.getElementById('errorAlert');
        
        if (alerta) {
            alerta.textContent = mensaje;
            alerta.classList.remove('d-none');
            console.log("✅ Alerta éxito mostrada");
        } else {
            console.error("❌ No se encontró #successAlert en el DOM");
        }
        
        if (errorAlerta) {
            errorAlerta.classList.add('d-none');
        }
        
        // Ocultar alerta después de 5 segundos
        setTimeout(() => {
            if (alerta) alerta.classList.add('d-none');
        }, 5000);
    }

    function mostrarError(mensaje) {
        console.log("❌ MOSTRAR ERROR:", mensaje);
        const alerta = document.getElementById('errorAlert');
        const successAlerta = document.getElementById('successAlert');
        
        if (alerta) {
            alerta.textContent = mensaje;
            alerta.classList.remove('d-none');
            console.log("✅ Alerta error mostrada");
        } else {
            console.error("❌ No se encontró #errorAlert en el DOM");
        }
        
        if (successAlerta) {
            successAlerta.classList.add('d-none');
        }
        
        // Ocultar alerta después de 5 segundos
        setTimeout(() => {
            if (alerta) alerta.classList.add('d-none');
        }, 5000);
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
    // Verificación de RUT existente - MEJORADO
    // ==============================
    const rutInput = document.getElementById('rut');
    if (rutInput) {
        rutInput.addEventListener('blur', async function () {
            const rut = this.value.trim();
            if (!rut) {
                document.getElementById('datosChoferNuevo').style.display = 'none';
                return;
            }

            // Validación básica de RUT
            const rutRegex = /^\d{1,2}(\.\d{3}){2}-[\dkK]$|^\d{7,8}-[\dkK]$/;
            if (!rutRegex.test(rut)) {
                mostrarError("Formato de RUT inválido (ej: 12.345.678-9 o 12345678-9).");
                document.getElementById('datosChoferNuevo').style.display = 'none';
                return;
            }

            try {
                const res = await fetch(`/api/autenticacion/existe/?rut=${encodeURIComponent(rut)}`);
                if (!res.ok) throw new Error('Error en la respuesta del servidor');
                
                const data = await res.json();
                
                if (data.existe) {
                    // RUT existe, ocultar formulario de nuevo chofer
                    document.getElementById('datosChoferNuevo').style.display = 'none';
                    mostrarExito("✅ Chofer encontrado en el sistema.");
                } else {
                    // RUT no existe, mostrar formulario de nuevo chofer
                    document.getElementById('datosChoferNuevo').style.display = 'block';
                    // Prellenar el RUT en el formulario de nuevo chofer
                    document.getElementById('rutChoferNuevo').value = rut;
                    // Establecer cargo por defecto como CHOFER
                    document.getElementById('cargoChofer').value = 'CHOFER';
                    mostrarError("⚠️ Este RUT no está registrado. Complete los datos del nuevo chofer.");
                }
            } catch (err) {
                console.error("Error al verificar RUT:", err);
                mostrarError("Error al verificar RUT en el sistema.");
            }
        });
    }

    // ==============================
    // Registro de nuevo chofer - MEJORADO
    // ==============================
    const registrarBtn = document.getElementById('registrarChoferBtn');
    if (registrarBtn) {
        registrarBtn.addEventListener('click', async () => {
            const nuevoChofer = {
                rut: document.getElementById('rutChoferNuevo')?.value.trim() || document.getElementById('rut').value.trim(),
                nombre: document.getElementById('nombreChofer').value.trim(),
                cargo: document.getElementById('cargoChofer').value, // Ya viene como CHOFER por defecto
                region: document.getElementById('regionChofer').value.trim(),
                horario: document.getElementById('horarioChofer').value.trim(),
                disponibilidad: document.getElementById('disponibleChofer').checked,
                usuario: document.getElementById('usuarioChofer').value.trim(),
                password: document.getElementById('passwordChofer').value.trim() || "temporal123",
                taller_id: 1  // Asegurar que tenga un taller por defecto
            };

            // Validación de campos obligatorios
            if (!nuevoChofer.rut || !nuevoChofer.nombre || !nuevoChofer.usuario || !nuevoChofer.password) {
                mostrarError("Completa todos los campos obligatorios del chofer (RUT, Nombre, Usuario y Contraseña).");
                return;
            }

            if (nuevoChofer.password.length < 6) {
                mostrarError("La contraseña debe tener al menos 6 caracteres.");
                return;
            }

            // Validar formato de RUT
            const rutRegex = /^\d{1,2}(\.\d{3}){2}-[\dkK]$|^\d{7,8}-[\dkK]$/;
            if (!rutRegex.test(nuevoChofer.rut)) {
                mostrarError("Formato de RUT inválido (ej: 12.345.678-9 o 12345678-9).");
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
                    mostrarExito("✅ Chofer registrado correctamente. Ahora puedes completar el ingreso del vehículo.");
                    document.getElementById('datosChoferNuevo').style.display = 'none';
                    // Limpiar el formulario de nuevo chofer
                    document.getElementById('nombreChofer').value = '';
                    document.getElementById('regionChofer').value = '';
                    document.getElementById('horarioChofer').value = '';
                    document.getElementById('usuarioChofer').value = '';
                    document.getElementById('passwordChofer').value = '';
                    document.getElementById('disponibleChofer').checked = true;
                } else {
                    mostrarError(data.message || "Error al registrar chofer. Verifica los datos.");
                }

            } catch (error) {
                console.error("Error al registrar chofer:", error);
                mostrarError("Error de conexión al registrar chofer. Intenta nuevamente.");
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
            if (!patente) {
                document.getElementById('datosVehiculoNuevo').style.display = 'none';
                return;
            }

            try {
                const res = await fetch(`/vehiculos/existe/?patente=${encodeURIComponent(patente)}`);
                const data = await res.json();
                document.getElementById('datosVehiculoNuevo').style.display = !data.existe ? 'block' : 'none';
            } catch (err) {
                console.error("Error al verificar patente:", err);
            }
        });
    }

    // ==============================
    // Formulario de ingreso de vehículo - CORREGIDO
    // ==============================
    const form = document.getElementById('ingresoForm');
    if (form) {
        form.addEventListener('submit', async function (e) {
            e.preventDefault();
            console.log("✅ Formulario enviado");

            const data = {
                patente: document.getElementById('patente')?.value.trim(),
                fecha: document.getElementById('fechaSeleccionada')?.value.trim(),
                hora: document.getElementById('horaSeleccionada')?.value.trim(),
                rut: document.getElementById('rut')?.value.trim(),
                tipo_mantenimiento: document.getElementById('tipoMantenimiento')?.value,
                kilometraje: document.getElementById('kilometraje')?.value,
                descripcion: document.getElementById('descripcion')?.value
            };

            console.log("📦 Datos a enviar:", data);

            // Validaciones básicas - REGEX CORREGIDO
            const patenteRegex = /^[A-Z]{2,4}\d{2,3}$/i;  // ✅ Permite 2-4 letras y 2-3 números
            const rutRegex = /^\d{1,2}(\.\d{3}){2}-[\dkK]$|^\d{7,8}-[\dkK]$/;

            if (!patenteRegex.test(data.patente)) {
                mostrarError("Formato de patente inválido (ej: AB1234, ABC12 o ABCD12).");  // ✅ Mensaje actualizado
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

            console.log("✅ Pasó todas las validaciones");

            // ✅ CORRECCIÓN: Verificación correcta de vehículo nuevo
            const datosVehiculoNuevo = document.getElementById('datosVehiculoNuevo');
            if (datosVehiculoNuevo && datosVehiculoNuevo.style.display !== 'none') {
                console.log("🚗 Vehículo nuevo detectado");
                data.marca = document.getElementById('marca').value.trim();
                data.modelo = document.getElementById('modelo').value.trim();
                data.anio = document.getElementById('anio').value.trim();
                data.tipo_vehiculo = document.getElementById('tipo').value.trim();
                data.ubicacion = document.getElementById('ubicacion').value;
                
                console.log("📋 Datos vehículo nuevo:", {
                    marca: data.marca,
                    modelo: data.modelo,
                    anio: data.anio,
                    tipo_vehiculo: data.tipo_vehiculo,
                    ubicacion: data.ubicacion
                });
                
                if (!data.ubicacion) {
                    console.log("❌ Falta ubicación");
                    mostrarError("Debes seleccionar una ubicación/taller.");
                    return;
                }
                if (!data.marca || !data.modelo || !data.anio || !data.tipo_vehiculo || !data.ubicacion) {
                    console.log("❌ Faltan datos del vehículo nuevo");
                    mostrarError("Completa todos los datos del vehículo nuevo.");
                    return;
                }
            } else {
                console.log("🚗 Vehículo existente");
            }

            console.log("🌐 Enviando datos al servidor...");

            try {
                const res = await fetch("/api/ordenestrabajo/registrar/", {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify(data)
                });
                
                console.log("✅ Status de respuesta:", res.status);
                console.log("✅ OK:", res.ok);
                
                // Verifica si la respuesta es JSON válido
                const responseText = await res.text();
                console.log("📨 Respuesta texto:", responseText);
                
                let response;
                try {
                    response = JSON.parse(responseText);
                    console.log("📨 Respuesta JSON parseada:", response);
                } catch (parseError) {
                    console.error("❌ Error parseando JSON:", parseError);
                    mostrarError("Error en la respuesta del servidor");
                    return;
                }

                if (response.status === "nuevo_chofer") {
                    console.log("🆕 Nuevo chofer detectado");
                    mostrarError(response.message);
                    document.getElementById('datosChoferNuevo').style.display = 'block';
                } else if (response.status === "ok") {
                    console.log("✅ Registro exitoso");
                    mostrarExito(response.message);
                    form.reset();
                    document.getElementById('datosVehiculoNuevo').style.display = 'none';
                    document.getElementById('datosChoferNuevo').style.display = 'none';
                    if (!fechasOcupadas[data.fecha]) fechasOcupadas[data.fecha] = [];
                    fechasOcupadas[data.fecha].push(data.hora);
                    selectedDate = null;
                    selectedTime = null;
                    generateCalendar();
                    updateTimeSlots();
                    document.getElementById('scheduleSummary').style.display = 'none';
                } else if (response.status === "redirect") {
                    console.log("🔄 Redirección requerida");
                    mostrarError(response.message);
                    setTimeout(() => { window.location.href = response.redirect_url; }, 2500);
                } else {
                    console.log("❌ Respuesta inesperada:", response);
                    mostrarError(response.message || "Error al registrar");
                }
            } catch (err) {
                console.error("❌ Error en el fetch:", err);
                mostrarError("Error de conexión con el servidor.");
            }
        });
    }
});