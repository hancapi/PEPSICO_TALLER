// static/js/auth.js - Protección universal + roles + badge + creador dinámico
document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ auth.js cargado correctamente");

  const isLocal = ["localhost", "127.0.0.1"].includes(window.location.hostname);
  const isLoginPage = window.location.pathname.includes("inicio-sesion");
  const envIndicator = document.getElementById("envIndicator");
  const logoutButton = document.getElementById("logoutButton");

  // ===== Verificar autenticación =====
  function checkAuth() {
    const token = localStorage.getItem("token");
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
        // Soportar info de recinto/taller si viene en el payload
        const t = empleado.taller || {};
        const recintoNombre = t.nombre || "No asignado";
        const recintoUbicacion = t.ubicacion || "-";

        empleadoInfo.innerHTML = `
          <div class="col-md-6">
            <table class="table table-sm">
              <tr><td><strong>RUT:</strong></td><td>${empleado.rut}</td></tr>
              <tr><td><strong>Cargo:</strong></td><td>${empleado.cargo}</td></tr>
              <tr><td><strong>Región:</strong></td><td>${empleado.region}</td></tr>
              <tr><td><strong>Recinto:</strong></td><td>${recintoNombre} (${recintoUbicacion})</td></tr>
            </table>
          </div>
          <div class="col-md-6">
            <table class="table table-sm">
              <tr><td><strong>Horario:</strong></td><td>${empleado.horario}</td></tr>
              <tr>
                <td><strong>Disponibilidad:</strong></td>
                <td>${
                  empleado.disponibilidad
                    ? '<span class="badge bg-success">Disponible</span>'
                    : '<span class="badge bg-danger">Ocupado</span>'
                }</td>
              </tr>
            </table>
          </div>`;
      }

      aplicarPermisos(empleado);
      actualizarBadgeRol(empleado);
      actualizarCreadorOT(empleado);

    } catch (error) {
      console.error("❌ Error al cargar datos del usuario:", error);
    }
  }

  // ===== Mostrar badge de rol =====
  function actualizarBadgeRol(empleado) {
    const roleBadge = document.getElementById("roleBadge");
    if (!roleBadge) return;
    const cargo = (empleado.cargo || "").toLowerCase();
    const colorMap = {
      chofer: "bg-primary",
      mecanico: "bg-warning text-dark",
      supervisor: "bg-success",
      administrativo: "bg-info text-dark"
    };
    roleBadge.className = `badge ${colorMap[cargo] || "bg-secondary"} text-uppercase fade-in`;
    roleBadge.textContent = `Rol: ${empleado.cargo}`;
  }

  // ===== Mostrar quién crea la OT (en ingreso_vehiculos.html) =====
  function actualizarCreadorOT(empleado) {
    const creatorInfo = document.getElementById("creatorInfo");
    if (creatorInfo) {
      creatorInfo.innerHTML = `Crearás como: <strong>${empleado.rut}</strong> (${empleado.cargo})`;
    }
  }

  // ===== Permisos =====
  const PERMISOS = {
    chofer: ["inicio", "ingreso_vehiculos"],
    supervisor: ["inicio", "registro_taller", "ingreso_vehiculos", "reportes", "ficha_vehiculo"],
    mecanico: ["inicio", "registro_taller", "ficha_vehiculo"],
    administrativo: ["inicio", "reportes"],
  };

  function tienePermiso(cargo, permiso) {
    const rol = (cargo || "").toLowerCase();
    return PERMISOS[rol] && PERMISOS[rol].includes(permiso);
  }

  function aplicarPermisos(empleado) {
    const cargo = (empleado.cargo || "").toLowerCase();

    // --- Sidebar ---
    document.querySelectorAll(".nav-link").forEach((link) => {
      const href = link.getAttribute("href") || "";

      if (href.includes("vehiculos") && !tienePermiso(cargo, "ingreso_vehiculos"))
        link.style.display = "none";

      // Ojo: aquí se asume que las rutas de taller contienen "taller"
      if (href.includes("taller") && !tienePermiso(cargo, "registro_taller"))
        link.style.display = "none";

      if (href.includes("reportes") && !tienePermiso(cargo, "reportes"))
        link.style.display = "none";
    });

    // --- Tarjetas del Dashboard ---
    document.querySelectorAll(".card.feature-card").forEach((card) => {
      const title = (card.querySelector(".card-title")?.textContent || "").toLowerCase();

      if (title.includes("registro taller") && !tienePermiso(cargo, "registro_taller"))
        card.style.display = "none";
      if (title.includes("ingreso vehículos") && !tienePermiso(cargo, "ingreso_vehiculos"))
        card.style.display = "none";
      if (title.includes("ficha vehículo") && !tienePermiso(cargo, "ficha_vehiculo"))
        card.style.display = "none";
      if (title.includes("reportes") && !tienePermiso(cargo, "reportes"))
        card.style.display = "none";
    });
  }

  // ===== Logout =====
  function cerrarSesion() {
    localStorage.clear();
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
