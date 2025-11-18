// static/js/dashboard.js - KPIs del dashboard principal

async function loadDashboardStats() {
    try {
        // Ruta correcta según autenticacion/urls.py
        const res = await fetch('/autenticacion/dashboard-stats/');
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);

        const data = await res.json();
        const k = data.kpis || {};

        document.getElementById("statVehiculos").textContent = k.total_vehiculos ?? 0;
        document.getElementById("statTaller").textContent = k.en_taller ?? 0;
        document.getElementById("statProceso").textContent = k.en_proceso ?? 0;
        document.getElementById("statEmpleados").textContent = k.total_empleados ?? 0;

    } catch (err) {
        console.error("❌ Error al cargar stats del dashboard:", err);
    }
}

// Cargar una vez al entrar
document.addEventListener("DOMContentLoaded", loadDashboardStats);

// Actualizar cada 5 segundos
setInterval(loadDashboardStats, 5000);
