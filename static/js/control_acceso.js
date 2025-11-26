// static/js/control_acceso.js
// Lógica UI del modal de ingreso en Control de Acceso

document.addEventListener("DOMContentLoaded", () => {
    const rutInput = document.getElementById("rut_chofer_modal");
    const rutSugeridoInput = document.getElementById("rut_sugerido_hidden");
    const wrapperForzar = document.getElementById("wrapper_forzar_modal");
    const wrapperMotivo = document.getElementById("wrapper_motivo_modal");

    if (!rutInput || !wrapperForzar || !wrapperMotivo) {
        return; // nada que hacer
    }

    const rutSugerido = rutSugeridoInput ? (rutSugeridoInput.value || "").trim() : "";

    function normalizarRut(rut) {
        if (!rut) return "";
        return rut.replace(/\./g, "")
                  .replace(/-/g, "")
                  .trim()
                  .toUpperCase();
    }

    function actualizarVisibilidadForzado() {
        const rutIngresado = normalizarRut(rutInput.value);
        const rutSug = normalizarRut(rutSugerido);

        // Si no hay RUT sugerido (no hay solicitud ni designación),
        // nunca mostramos forzar: se queda oculto.
        if (!rutSug) {
            wrapperForzar.classList.add("d-none");
            wrapperMotivo.classList.add("d-none");
            return;
        }

        // Si el guardia aún no escribe o coincide con el sugerido, ocultamos
        if (!rutIngresado || rutIngresado === rutSug) {
            wrapperForzar.classList.add("d-none");
            wrapperMotivo.classList.add("d-none");
        } else {
            // Si el RUT NO coincide con el sugerido -> mostrar bloque de forzado
            wrapperForzar.classList.remove("d-none");
            wrapperMotivo.classList.remove("d-none");
        }
    }

    // Al cargar (por si el campo viene pre-rellenado)
    actualizarVisibilidadForzado();

    // Cada vez que cambie el RUT
    rutInput.addEventListener("input", actualizarVisibilidadForzado);
});
