// static/js/pausas.js
async function pausaStart(otId, motivo = "Pausa iniciada") {
  const fd = new FormData();
  fd.append("motivo", motivo);
  const res = await fetch(`/api/ordenestrabajo/${otId}/pausas/start/`, { method: "POST", body: fd });
  const data = await res.json();
  if (!data.success) throw new Error(data.message || "Error al iniciar pausa");
  return data.pausa;
}

async function pausaStop(otId) {
  const res = await fetch(`/api/ordenestrabajo/${otId}/pausas/stop/`, { method: "POST" });
  const data = await res.json();
  if (!data.success) throw new Error(data.message || "Error al detener pausa");
  return data.pausa;
}

async function pausaList(otId) {
  const res = await fetch(`/api/ordenestrabajo/${otId}/pausas/`);
  const data = await res.json();
  if (!data.success) throw new Error(data.message || "Error al listar pausas");
  return data.pausas;
}
