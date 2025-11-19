# ordenestrabajo/api_views_estado.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from autenticacion.roles import mecanico_or_supervisor

from vehiculos.models import Vehiculo
from ordenestrabajo.models import OrdenTrabajo
from datetime import date

def normalize(p):
    return "" if not p else p.replace(".", "").replace("-", "").strip().upper()

@login_required
@mecanico_or_supervisor
def api_cambiar_estado(request):

    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Método no permitido"}, status=405)

    patente = normalize(request.POST.get("patente"))
    nuevo_estado = request.POST.get("estado")
    comentario = (request.POST.get("comentario") or "").strip()

    if not patente or not nuevo_estado:
        return JsonResponse({"success": False, "message": "Patente y estado son obligatorios"})

    if nuevo_estado == "Finalizado" and comentario == "":
        return JsonResponse({
            "success": False,
            "message": "Debe ingresar un comentario para finalizar."
        })

    veh = Vehiculo.objects.filter(patente=patente).first()
    if not veh:
        return JsonResponse({"success": False, "message": "Vehículo no existe."})

    ot = (
        OrdenTrabajo.objects.filter(
            patente_id=patente,
            estado__in=["Pendiente", "En Taller", "En Proceso", "Pausado"]
        )
        .order_by("-fecha_ingreso", "-hora_ingreso")
        .first()
    )

    if not ot:
        return JsonResponse({"success": False, "message": "No hay OT activa para actualizar."})

    TRANSICIONES_VALIDAS = {
        "Pendiente": ["En Taller"],
        "En Taller": ["En Proceso", "Pausado"],
        "En Proceso": ["Pausado", "Finalizado"],
        "Pausado": ["En Taller", "En Proceso", "Finalizado"],
    }

    if nuevo_estado not in TRANSICIONES_VALIDAS.get(ot.estado, []):
        return JsonResponse({
            "success": False,
            "message": f"No se puede cambiar de {ot.estado} a {nuevo_estado}"
        })

    ot.estado = nuevo_estado
    ot.descripcion = (ot.descripcion or "") + f"\n[{request.user.username}] {comentario}"

    if nuevo_estado == "Finalizado":
        ot.fecha_salida = date.today()
        veh.estado = "Disponible"
    else:
        veh.estado = nuevo_estado

    veh.save()
    ot.save()

    return JsonResponse({"success": True, "message": "Estado actualizado correctamente."})
