# ordenestrabajo/api_views_estado.py
from datetime import date

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

from autenticacion.models import Empleado
from autenticacion.roles import mecanico_or_supervisor
from vehiculos.models import Vehiculo
from ordenestrabajo.models import OrdenTrabajo


def normalize(patente: str) -> str:
    """
    Normaliza la patente:
    - Elimina puntos y guiones.
    - Quita espacios.
    - Convierte a mayúsculas.
    """
    return "" if not patente else patente.replace(".", "").replace("-", "").strip().upper()


@login_required
@mecanico_or_supervisor
def api_cambiar_estado(request):
    """
    Cambia el estado de la última OT ACTIVA asociada a una patente.

    Reglas de transición principales:

    - Pendiente  -> En Taller  (RECIBIR vehículo; requiere que el guardia lo haya ingresado al recinto)
    - Recibida   -> En Proceso, Pausado
    - En Taller  -> En Proceso, Pausado
    - En Proceso -> Pausado, Finalizado, No Reparable, Sin Repuestos
    - Pausado    -> En Taller, En Proceso, No Reparable, Sin Repuestos
                    (NO puede ir a Finalizado)

    Estados finales: Finalizado, No Reparable, Sin Repuestos
      - Se setea fecha_salida.
      - El vehículo queda en estado "Disponible".

    Estados de trabajo en taller: Recibida, En Taller, En Proceso, Pausado
      - El vehículo queda en estado "En Taller".

    🔹 Comentario: obligatorio en cualquier cambio de estado.
    """

    if request.method != "POST":
        return JsonResponse(
            {"success": False, "message": "Método no permitido"},
            status=405,
        )

    patente = normalize(request.POST.get("patente"))
    nuevo_estado = (request.POST.get("estado") or "").strip()
    comentario = (request.POST.get("comentario") or "").strip()

    if not patente or not nuevo_estado:
        return JsonResponse(
            {"success": False, "message": "Patente y estado son obligatorios"}
        )

    # =============================
    #  Estados finales
    # =============================
    ESTADOS_FINALES = ["Finalizado", "No Reparable", "Sin Repuestos"]

    # =============================
    #  Comentario obligatorio SIEMPRE
    # =============================
    if comentario == "":
        return JsonResponse(
            {
                "success": False,
                "message": "Debe ingresar un comentario para cambiar el estado.",
            }
        )

    veh = Vehiculo.objects.filter(patente=patente).first()
    if not veh:
        return JsonResponse(
            {"success": False, "message": "Vehículo no existe."}
        )

    # Estados considerados "activos" para buscar la OT vigente
    ESTADOS_ACTIVOS = ["Pendiente", "Recibida", "En Taller", "En Proceso", "Pausado"]

    ot = (
        OrdenTrabajo.objects.filter(
            patente_id=patente,
            estado__in=ESTADOS_ACTIVOS,
        )
        .select_related("patente")
        .order_by("-fecha_ingreso", "-hora_ingreso")
        .first()
    )

    if not ot:
        return JsonResponse(
            {"success": False, "message": "No hay OT activa para actualizar."}
        )

    # =============================
    #  Nombre y cargo del empleado que hace el cambio
    # =============================
    empleado = Empleado.objects.filter(usuario=request.user.username).first()

    display_nombre = (
        empleado.nombre
        if empleado and empleado.nombre
        else (request.user.get_full_name() or request.user.username)
    )

    if empleado and empleado.cargo:
        cargo_raw = empleado.cargo.upper()
        if cargo_raw == "MECANICO":
            cargo_label = "Mecánico"
        elif cargo_raw == "SUPERVISOR":
            cargo_label = "Supervisor"
        else:
            cargo_label = empleado.cargo.title()
    else:
        cargo_label = "Usuario"

    # Formato final: [Supervisor Nicolás] / [Mecánico Harol] / [Usuario pepito]
    autor_tag = f"[{cargo_label} {display_nombre}]"

    # =============================
    #  Matriz de transiciones
    # =============================
    TRANSICIONES_VALIDAS = {
        # 👉 ahora sí se permite Pendiente -> En Taller (RECIBIR),
        #    pero validaremos además que el vehículo esté En Recinto.
        "Pendiente": ["En Taller"],
        "Recibida": ["En Proceso", "Pausado"],
        "En Taller": ["En Proceso", "Pausado"],
        "En Proceso": ["Pausado", "Finalizado", "No Reparable", "Sin Repuestos"],
        "Pausado": ["En Taller", "En Proceso", "No Reparable", "Sin Repuestos"],
    }

    if nuevo_estado not in TRANSICIONES_VALIDAS.get(ot.estado, []):
        return JsonResponse(
            {
                "success": False,
                "message": f"No se puede cambiar de {ot.estado} a {nuevo_estado}",
            }
        )

    # =============================
    #  Regla extra:
    #  Pendiente -> En Taller SOLO si el vehículo está dentro del recinto
    #  (En Recinto) o, por compatibilidad, ya En Taller.
    # =============================
    if ot.estado == "Pendiente" and nuevo_estado == "En Taller":
        if veh.estado not in ["En Recinto", "En Taller"]:
            return JsonResponse(
                {
                    "success": False,
                    "message": (
                        "No se puede recibir el vehículo en taller porque aún no ha sido "
                        "ingresado al recinto por el guardia (estado del vehículo: "
                        f"{veh.estado})."
                    ),
                }
            )

    # =============================
    #  Actualizar OT y Vehículo
    # =============================
    ot.estado = nuevo_estado

    # Agregar comentario a la bitácora de la OT (cargo + nombre)
    if comentario:
        base = (ot.descripcion or "").rstrip()
        prefix = "\n" if base else ""
        new_desc = f"{base}{prefix}{autor_tag} {comentario}"

        # 🔐 Truncar para no reventar el max_length de la columna
        max_len = OrdenTrabajo._meta.get_field("descripcion").max_length
        if max_len:
            new_desc = new_desc[:max_len]

        ot.descripcion = new_desc

    # Estados finales cierran la OT
    if nuevo_estado in ESTADOS_FINALES:
        ot.fecha_salida = date.today()
        veh.estado = "Disponible"
    # Estados de trabajo en taller
    elif nuevo_estado in ["Recibida", "En Taller", "En Proceso", "Pausado"]:
        veh.estado = "En Taller"
    else:
        # Fallback defensivo
        veh.estado = nuevo_estado

    veh.save()
    ot.save()

    return JsonResponse(
        {"success": True, "message": "Estado actualizado correctamente."}
    )
