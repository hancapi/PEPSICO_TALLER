// static/js/pausas.js

// Helper CSRF (igual que en otros JS)
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    for (const cookie of document.cookie.split(";")) {
      const c = cookie.trim();
      if (c.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(c.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const csrftoken = getCookie("csrftoken");

/**
 * Inicia una pausa para la OT dada.
 * La vista Django devuelve: { success, pausa_id, inicio }
 */
async function pausaStart(otId, motivo = "Pausa iniciada") {
  const fd = new FormData();
  fd.append("motivo", motivo); // el backend hoy no lo usa, pero no molesta

  const res = await fetch(`/api/ordenestrabajo/${otId}/pausas/start/`, {
    method: "POST",
    body: fd,
    credentials: "same-origin",
    headers: {
      "X-CSRFToken": csrftoken,
      "X-Requested-With": "XMLHttpRequest",
    },
  });

  const data = await res.json();

  if (!res.ok || !data.success) {
    throw new Error(data.message || "Error al iniciar pausa");
  }

  // Normalizamos lo que devolvemos al front
  return {
    id: data.pausa_id,
    inicio: data.inicio,
  };
}

/**
 * Detiene la pausa activa de la OT dada.
 * La vista Django devuelve: { success, pausa_id, inicio, fin }
 */
async function pausaStop(otId) {
  const res = await fetch(`/api/ordenestrabajo/${otId}/pausas/stop/`, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "X-CSRFToken": csrftoken,
      "X-Requested-With": "XMLHttpRequest",
    },
  });

  const data = await res.json();

  if (!res.ok || !data.success) {
    throw new Error(data.message || "Error al detener pausa");
  }

  return {
    id: data.pausa_id,
    inicio: data.inicio,
    fin: data.fin,
  };
}

/**
 * Lista pausas de una OT.
 * Suponemos una API JSON en /api/ordenestrabajo/<otId>/pausas/
 * que devuelve: { success, pausas: [...] }
 */
async function pausaList(otId) {
  const res = await fetch(`/api/ordenestrabajo/${otId}/pausas/`, {
    credentials: "same-origin",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
    },
  });

  const data = await res.json();

  if (!res.ok || !data.success) {
    throw new Error(data.message || "Error al listar pausas");
  }

  return data.pausas || [];
}
