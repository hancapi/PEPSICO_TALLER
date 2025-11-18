// static/js/dashboard.js - KPIs del dashboard principal
async function loadDashboardStats() {
  try {
    const res = await fetch('/api/autenticacion/dashboard-stats/');
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    const data = await res.json();

    // Corrige acceso a los valores reales dentro de "kpis"
    const k = data.kpis || {};

    document.getElementById("statVehiculos").textContent = k.total_vehiculos ?? 0;
    document.getElementById("statTaller").textContent = k.en_taller ?? 0;
    document.getElementById("statProceso").textContent = k.en_proceso ?? 0;
    document.getElementById("statEmpleados").textContent = k.total_empleados ?? 0;
  } catch (err) {
    console.error("❌ Error al cargar stats del dashboard:", err);
  }
}

document.addEventListener("DOMContentLoaded", loadDashboardStats);
