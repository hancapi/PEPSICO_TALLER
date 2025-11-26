// static/js/dashboard.js - KPIs del dashboard principal

async function loadDashboardStats() {
    try {
        // Ruta correcta según autenticacion/urls.py
        const res = await fetch('/autenticacion/dashboard-stats/', {
            credentials: "same-origin",
        });
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);

        const data = await res.json();
        const k = data.kpis || {};

        const elVeh   = document.getElementById("statVehiculos");
        const elTall  = document.getElementById("statTaller");
        const elProc  = document.getElementById("statProceso");
        const elEmpl  = document.getElementById("statEmpleados");

        if (elVeh)  elVeh.textContent  = k.total_vehiculos ?? 0;
        if (elTall) elTall.textContent = k.en_taller ?? 0;
        if (elProc) elProc.textContent = k.en_proceso ?? 0;
        if (elEmpl) elEmpl.textContent = k.total_empleados ?? 0;

    } catch (err) {
        console.error("❌ Error al cargar stats del dashboard:", err);
    }
}

// Cargar una vez al entrar
document.addEventListener("DOMContentLoaded", loadDashboardStats);

// Actualizar cada 5 segundos
setInterval(loadDashboardStats, 5000);
