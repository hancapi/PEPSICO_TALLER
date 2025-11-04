// dashboard.js 
async function loadDashboardStats() {
    try {
        const res = await fetch('/api/autenticacion/dashboard-stats/');
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();

        document.getElementById("statVehiculos").textContent = data.total_vehiculos;
        document.getElementById("statTaller").textContent = data.en_taller;
        document.getElementById("statProceso").textContent = data.en_proceso;
        document.getElementById("statEmpleados").textContent = data.total_empleados;
    } catch (err) {
        console.error("Error al cargar stats del dashboard:", err);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadDashboardStats();
});

