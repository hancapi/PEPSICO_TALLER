// login.js – Exclusivo para la página inicio-sesion.html

document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ login.js cargado correctamente");

  const isLocal = ["localhost", "127.0.0.1"].includes(window.location.hostname);
  const API_BASE_URL = isLocal
    ? "http://localhost:8000/api"
    : "https://testeorepocaps.loca.lt/api";
  const AUTH_API_URL = `${API_BASE_URL}/autenticacion`;

  const loginForm = document.getElementById("loginForm");
  const loginButton = document.getElementById("loginButton");
  const loadingSpinner = document.getElementById("loadingSpinner");
  const buttonText = document.getElementById("buttonText");
  const errorAlert = document.getElementById("errorAlert");
  const errorMessage = document.getElementById("errorMessage");
  const successAlert = document.getElementById("successAlert");
  const successMessage = document.getElementById("successMessage");
  const serverStatus = document.getElementById("serverStatus");
  const dbStatus = document.getElementById("dbStatus");
  const envIndicator = document.getElementById("envIndicator");

  if (envIndicator) {
    envIndicator.innerHTML = isLocal
      ? "🌐 Entorno local activo"
      : "🚀 Conectado al túnel remoto";
  }

  // ==== Utilidades ====
  const showError = (msg) => {
    if (errorMessage && errorAlert) {
      errorMessage.textContent = msg;
      errorAlert.style.display = "block";
      successAlert.style.display = "none";
    }
  };

  const showSuccess = (msg) => {
    if (successMessage && successAlert) {
      successMessage.textContent = msg;
      successAlert.style.display = "block";
      errorAlert.style.display = "none";
    }
  };

  const setLoading = (isLoading) => {
    if (loadingSpinner && buttonText && loginButton) {
      loadingSpinner.style.display = isLoading ? "inline-block" : "none";
      buttonText.textContent = isLoading
        ? " Verificando..."
        : "🔐 Ingresar al Sistema";
      loginButton.disabled = isLoading;
    }
  };

  // ==== Verificar estado del servidor ====
  async function checkStatus() {
    try {
      const res = await fetch(`${AUTH_API_URL}/status/`);
      const data = await res.json();

      if (serverStatus) {
        serverStatus.textContent = "Conectado ✅";
        serverStatus.className = "badge bg-success";
      }

      if (dbStatus) {
        if (data.database.includes("Error")) {
          dbStatus.textContent = "Error BD";
          dbStatus.className = "badge bg-danger";
        } else {
          dbStatus.textContent = data.database;
          dbStatus.className = "badge bg-success";
        }
      }
    } catch {
      if (serverStatus) {
        serverStatus.textContent = "Desconectado ❌";
        serverStatus.className = "badge bg-danger";
      }
      if (dbStatus) {
        dbStatus.textContent = "Error BD";
        dbStatus.className = "badge bg-danger";
      }
    }
  }

  setTimeout(checkStatus, 500);

  // ==== Envío del formulario ====
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const usuario = document.getElementById("usuario").value.trim();
      const contrasena = document.getElementById("contrasena").value.trim();

      if (!usuario || !contrasena) {
        showError("Complete todos los campos");
        return;
      }

      setLoading(true);

      try {
        const res = await fetch(`${AUTH_API_URL}/login/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ usuario, contrasena }),
        });

        const data = await res.json();

        if (data.success && data.empleado) {
          localStorage.setItem("usuarioData", JSON.stringify(data.empleado));
          localStorage.setItem("token", "authenticated");
          showSuccess(`✅ Bienvenido ${data.empleado.nombre}`);
          setTimeout(() => (window.location.href = "/inicio/"), 1000);
        } else {
          showError(data.message || "Usuario o contraseña incorrectos");
        }
      } catch (err) {
        console.error(err);
        showError("Error de conexión al servidor");
      } finally {
        setLoading(false);
      }
    });
  }
});
