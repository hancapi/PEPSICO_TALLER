// static/js/documentos.js
(() => {
  console.log("✅ documentos.js cargado");

  const isLocal = ["localhost", "127.0.0.1"].includes(window.location.hostname);
  const API_BASE = isLocal ? "http://localhost:8000/api" : "https://testeorepocaps.loca.lt/api";
  const API_DOCS = `${API_BASE}/documentos`;

  /**
   * Sube un documento al backend.
   * @param {{file: File, titulo: string, tipo: string, otId?: string|null, patente?: string|null}} payload
   */
  async function documentosUpload({ file, titulo, tipo, otId = null, patente = null }) {
    if (!file) throw new Error("Archivo requerido");
    if (!titulo) throw new Error("Título requerido");
    if (!otId && !patente) throw new Error("Debe indicar OT o Patente");

    const fd = new FormData();
    fd.append("archivo", file);
    fd.append("titulo", titulo);
    fd.append("tipo", tipo || "OTRO");
    if (otId) fd.append("ot_id", otId);
    if (patente) fd.append("patente", patente);

    const res = await fetch(`${API_DOCS}/upload/`, { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || `Error HTTP ${res.status}`);
    }
    return data.documento;
  }

  /**
   * Lista documentos por ot_id o patente (uno de los dos).
   */
  async function documentosList({ otId = null, patente = null }) {
    const params = new URLSearchParams();
    if (otId) params.append("ot_id", otId);
    if (patente) params.append("patente", patente);
    if (!otId && !patente) throw new Error("Debe indicar ot_id o patente");

    const res = await fetch(`${API_DOCS}/?${params.toString()}`);
    const data = await res.json();
    if (!res.ok || !data.success) {
      throw new Error(data.message || `Error HTTP ${res.status}`);
    }
    return data.documentos;
  }

  // Exponer helpers globalmente
  window.documentosUpload = documentosUpload;
  window.documentosList = documentosList;
})();
