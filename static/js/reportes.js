// static/js/reportes.js
(function () {

  document.addEventListener("DOMContentLoaded", () => {
    console.log("📊 Cargando reportes (reportes.js)...");

    loadKPIs();
    loadTalleres();
    loadTiempos();
  });

  // ====================================================
  // 1) KPIs Globales
  // ====================================================
  async function loadKPIs() {
    try {
      const res = await fetch("/reportes/api/resumen/", {
        credentials: "same-origin",
      });
      const data = await res.json();

      if (!res.ok || !data.success) {
        console.warn("Error KPIs:", data.message || res.status);
        return;
      }

      const d = data.data || {};
      const elVehTot = document.getElementById("kpi_vehiculos_totales");
      const elVehTal = document.getElementById("kpi_vehiculos_taller");
      const elOTAct  = document.getElementById("kpi_ordenes_activas");
      const elEmp    = document.getElementById("kpi_empleados");

      if (elVehTot) elVehTot.textContent = d.vehiculos_totales ?? "0";
      if (elVehTal) elVehTal.textContent = d.vehiculos_en_taller ?? "0";
      if (elOTAct)  elOTAct.textContent  = d.ordenes_activas ?? "0";
      if (elEmp)    elEmp.textContent    = d.empleados_activos ?? "0";

    } catch (e) {
      console.error("Error KPIs", e);
    }
  }

  // ====================================================
  // 2) Vehículos + OTs por Taller
  // ====================================================
  async function loadTalleres() {
    try {
      const res = await fetch("/reportes/api/talleres/", {
        credentials: "same-origin",
      });
      const data = await res.json();
      if (!res.ok || !data.success) {
        console.warn("Error talleres:", data.message || res.status);
        return;
      }

      const items = Array.isArray(data.items) ? data.items : [];

      const labels    = items.map((t) => t.nombre);
      const vehiculos = items.map((t) => t.vehiculos_total);
      const otsPend   = items.map((t) => t.ots_pendientes);
      const otsProc   = items.map((t) => t.ots_en_proceso);
      const otsFin    = items.map((t) => t.ots_finalizadas);

      const ctxVeh = document.getElementById("chartVehiculosTaller");
      const ctxOTs = document.getElementById("chartOTsTaller");

      if (ctxVeh && window.Chart) {
        new Chart(ctxVeh, {
          type: "bar",
          data: {
            labels: labels,
            datasets: [
              {
                label: "Vehículos",
                data: vehiculos,
                backgroundColor: "#007bff88",
                borderColor: "#007bff",
                borderWidth: 1,
              },
            ],
          },
        });
      }

      if (ctxOTs && window.Chart) {
        new Chart(ctxOTs, {
          type: "bar",
          data: {
            labels: labels,
            datasets: [
              {
                label: "Pendiente",
                data: otsPend,
                backgroundColor: "#ffc107aa",
                borderColor: "#ffc107",
                borderWidth: 1,
              },
              {
                label: "En Proceso",
                data: otsProc,
                backgroundColor: "#17a2b8aa",
                borderColor: "#17a2b8",
                borderWidth: 1,
              },
              {
                label: "Finalizado",
                data: otsFin,
                backgroundColor: "#28a745aa",
                borderColor: "#28a745",
                borderWidth: 1,
              },
            ],
          },
        });
      }
    } catch (e) {
      console.error("Error talleres", e);
    }
  }

  // ====================================================
  // 3) Tiempos Promedio
  // ====================================================
  async function loadTiempos() {
    try {
      const res = await fetch("/reportes/api/tiempos/", {
        credentials: "same-origin",
      });
      const data = await res.json();
      if (!res.ok || !data.success) {
        console.warn("Error tiempos:", data.message || res.status);
        return;
      }

      const porTaller = data.por_taller || {};
      const items = Object.values(porTaller);

      const labels  = items.map((t) => t.taller);
      const valores = items.map((t) => t.promedio_dias || 0);

      const ctx = document.getElementById("chartTiempos");
      if (!ctx || !window.Chart) return;

      new Chart(ctx, {
        type: "line",
        data: {
          labels: labels,
          datasets: [
            {
              label: "Promedio (días)",
              data: valores,
              tension: 0.3,
              borderColor: "#6610f2",
              backgroundColor: "#6610f244",
              borderWidth: 2,
              fill: true,
            },
          ],
        },
      });
    } catch (e) {
      console.error("Error tiempos", e);
    }
  }
})();
