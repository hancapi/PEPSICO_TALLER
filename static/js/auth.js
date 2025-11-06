// static/js/auth.js - Protección universal para todas las páginas excepto login

document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ auth.js cargado correctamente");

  const isLocal = ["localhost", "127.0.0.1"].includes(window.location.hostname);
  const isLoginPage = window.location.pathname.includes("inicio-sesion");
  const API_BASE_URL = isLocal
    ? "http://localhost:8000/api"
    : "https://testeorepocaps.loca.lt/api";

  const envIndicator = document.getElementById("envIndicator");
  const logoutButton = document.getElementById("logoutButton");

  // ===== Verificar autenticación =====
  function checkAuth() {
    const token = localStorage.getItem("token");
    const usuarioData = localStorage.getItem("usuarioData");

    if (!token && !isLoginPage) {
      console.warn("❌ No autenticado, redirigiendo al login...");
      window.location.href = "/inicio-sesion/";
      return false;
    }
    if (token && isLoginPage) {
      window.location.href = "/inicio/";
      return false;
    }
    return true;
  }

  // ===== Cargar datos del usuario =====
  function loadUserData() {
    const usuarioData = localStorage.getItem("usuarioData");
    if (!usuarioData) return;

    try {
      const empleado = JSON.parse(usuarioData);
      const welcomeTitle = document.getElementById("welcomeTitle");
      const empleadoInfo = document.getElementById("empleadoInfo");

      if (welcomeTitle)
        welcomeTitle.textContent = `Bienvenido, ${empleado.nombre}`;

      if (empleadoInfo) {
        empleadoInfo.innerHTML = `
          <div class="col-md-6">
            <table class="table table-sm">
              <tr><td><strong>RUT:</strong></td><td>${empleado.rut}</td></tr>
              <tr><td><strong>Cargo:</strong></td><td>${empleado.cargo}</td></tr>
              <tr><td><strong>Región:</strong></td><td>${empleado.region || 'No especificada'}</td></tr>
            </table>
          </div>
          <div class="col-md-6">
            <table class="table table-sm">
              <tr><td><strong>Horario:</strong></td><td>${empleado.horario || 'No especificado'}</td></tr>
              <tr><td><strong>Disponibilidad:</strong></td>
                <td><span class="badge badge-disponible">${mapDisponibilidad(empleado.disponibilidad)}</span></td></tr>
            </table>
          </div>`;
      }

      aplicarPermisos(empleado);
    } catch (error) {
      console.error("Error al cargar datos del usuario:", error);
    }
  }

  // ===== Permisos =====
  function tienePermiso(cargo, permiso) {
    const permisos = {
      chofer: ["inicio", "ingreso_vehiculos"],
      supervisor: ["inicio", "ingreso_vehiculos", "registro_taller", "reportes"],
      mecanico: ["inicio", "registro_taller", "reportes", "subir_documentos"],
      administrativo: ["inicio", "registro_taller", "reportes", "subir_documentos"],
    };
    const roleMap = { "mecánico": "mecanico" };
    const rol = roleMap[cargo.toLowerCase()] || cargo.toLowerCase();
    return permisos[rol] && permisos[rol].includes(permiso);
  }

  function aplicarPermisos(empleado) {
    const cargo = empleado.cargo.toLowerCase();

    document.querySelectorAll(".nav-link").forEach((link) => {
      const href = link.getAttribute("href");
      if (href.includes("vehiculos") && !tienePermiso(cargo, "ingreso_vehiculos"))
        link.parentElement.style.display = "none";
      if (href.includes("talleres") && !tienePermiso(cargo, "registro_taller"))
        link.parentElement.style.display = "none";
      if (href.includes("reportes") && !tienePermiso(cargo, "reportes"))
        link.parentElement.style.display = "none";
    });
  }

  // ===== Utilidades =====
  function mapDisponibilidad(value) {
    switch (Number(value)) {
      case 1:
        return "Disponible";
      case 2:
        return "Ocupado";
      case 3:
        return "Ausente";
      default:
        return "Desconocido";
    }
  }

  function cerrarSesion() {
    localStorage.removeItem("usuarioData");
    localStorage.removeItem("token");
    window.location.href = "/inicio-sesion/";
  }

  // ===== Inicialización =====
  if (checkAuth()) loadUserData();

  if (logoutButton) logoutButton.addEventListener("click", cerrarSesion);

  if (envIndicator && !isLoginPage)
    envIndicator.textContent = isLocal
      ? "🌐 Entorno local activo"
      : "🚀 Conectado al túnel remoto";
});
