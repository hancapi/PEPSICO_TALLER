// ============================================================
// login.js – Maneja autenticación desde inicio-sesion.html
// Versión estable con sesión Django real
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ login.js cargado correctamente");

  // --- Configuración de entorno ---
  const isLocal = ["localhost", "127.0.0.1"].includes(window.location.hostname);

  // 👇 Usamos el mismo prefijo que en urls.py global:
  // path('autenticacion/', include('autenticacion.urls', ...))
  const AUTH_API_URL = "/autenticacion";

  // --- Elementos del DOM ---
  const loginForm      = document.getElementById("loginForm");
  const loginButton    = document.getElementById("loginButton");
  const loadingSpinner = document.getElementById("loadingSpinner");
  const buttonText     = document.getElementById("buttonText");
  const errorAlert     = document.getElementById("errorAlert");
  const errorMessage   = document.getElementById("errorMessage");
  const successAlert   = document.getElementById("successAlert");
  const successMessage = document.getElementById("successMessage");
  const serverStatus   = document.getElementById("serverStatus");
  const dbStatus       = document.getElementById("dbStatus");
  const envIndicator   = document.getElementById("envIndicator");

  // --- Mostrar entorno ---
  if (envIndicator) {
    envIndicator.innerHTML = isLocal
      ? "🌐 Entorno local activo"
      : "🚀 Ejecutando en entorno remoto";
  }

  // ============================================================
  // Funciones de UI
  // ============================================================
  const showError = (msg) => {
    if (!errorAlert || !errorMessage || !successAlert) return;
    errorMessage.textContent = msg;
    errorAlert.classList.remove("d-none");
    successAlert.classList.add("d-none");
  };

  const showSuccess = (msg) => {
    if (!successAlert || !successMessage || !errorAlert) return;
    successMessage.textContent = msg;
    successAlert.classList.remove("d-none");
    errorAlert.classList.add("d-none");
  };

  const setLoading = (isLoading) => {
    if (!loginButton || !loadingSpinner || !buttonText) return;
    loginButton.disabled = isLoading;
    loadingSpinner.style.display = isLoading ? "inline-block" : "none";
    buttonText.textContent = isLoading
      ? " Verificando..."
      : "🔐 Ingresar al Sistema";
  };

  // ============================================================
  // Verificar estado del servidor
  // ============================================================
  async function checkStatus() {
    if (!serverStatus || !dbStatus) return;

    try {
      const res = await fetch(`${AUTH_API_URL}/status/`, {
        credentials: "same-origin",
      });
      const data = await res.json();

      serverStatus.textContent = "Conectado ✅";
      serverStatus.className = "badge bg-success";

      dbStatus.textContent = data.database || "OK";
      dbStatus.className = (data.database || "").includes("Error")
        ? "badge bg-danger"
        : "badge bg-success";
    } catch (err) {
      console.error("Error checkStatus:", err);
      serverStatus.textContent = "Desconectado ❌";
      serverStatus.className = "badge bg-danger";
      dbStatus.textContent = "Error BD";
      dbStatus.className = "badge bg-danger";
    }
  }

  setTimeout(checkStatus, 400);

  // ============================================================
  // Envío del formulario (LOGIN REAL vía API JSON)
  // ============================================================
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const usuario    = document.getElementById("usuario")?.value.trim() || "";
      const contrasena = document.getElementById("contrasena")?.value.trim() || "";

      if (!usuario || !contrasena) {
        showError("Complete todos los campos");
        return;
      }

      setLoading(true);

      try {
        const res = await fetch(`${AUTH_API_URL}/login/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
          body: JSON.stringify({ usuario, contrasena }),
        });

        const data = await res.json();

        if (res.ok && data.success) {
          localStorage.clear();
          if (data.empleado) {
            localStorage.setItem("usuarioData", JSON.stringify(data.empleado));
          }

          showSuccess(`✅ Bienvenido ${data.empleado?.nombre || usuario}`);
          console.log("👤 Sesión iniciada como:", data.empleado?.usuario || usuario);

          setTimeout(() => {
            window.location.replace("/inicio/");
          }, 600);
        } else {
          showError(data.message || "Usuario o contraseña incorrectos");
        }
      } catch (err) {
        console.error("❌ Error de conexión:", err);
        showError("Error de conexión al servidor");
      } finally {
        setLoading(false);
      }
    });
  }
});
