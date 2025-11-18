from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required

from autenticacion.models import Empleado
from ordenestrabajo.models import OrdenTrabajo
from vehiculos.models import Vehiculo


@login_required
def api_vehiculos_taller(request):
    user = request.user

    empleado = Empleado.objects.select_related("taller").filter(usuario=user.username).first()
    if not empleado:
        return JsonResponse({"error": "Empleado no encontrado"}, status=400)

    ot_activas = OrdenTrabajo.objects.filter(
        taller_id=empleado.taller.taller_id,
        estado__in=["Pendiente", "En Proceso", "En Taller"]
    )

    patentes = [ot.patente_id for ot in ot_activas]
    vehiculos = Vehiculo.objects.filter(patente__in=patentes)

    html = render_to_string("partials/tabla_vehiculos_taller.html", {
        "vehiculos": vehiculos
    })

    kpis = {
        "total_vehiculos": vehiculos.count(),
        "en_taller": vehiculos.filter(estado="En Taller").count(),
        "en_proceso": vehiculos.filter(estado="En Proceso").count(),
    }

    return JsonResponse({"kpis": kpis, "html": html})

@login_required
def api_mecanicos_por_taller(request):
    """
    Devuelve la lista de mecánicos pertenecientes al mismo taller del supervisor.
    """
    user = request.user
    supervisor = Empleado.objects.select_related("taller").filter(usuario=user.username).first()

    if not supervisor or not supervisor.taller_id:
        return JsonResponse({"success": False, "message": "No se pudo determinar tu taller."})

    mecanicos = (
        Empleado.objects
        .filter(
            cargo__iexact="MECANICO",
            taller_id=supervisor.taller_id,
            is_active=True
        )
        .values("rut", "nombre", "usuario")
    )

    return JsonResponse({
        "success": True,
        "mecanicos": list(mecanicos)
    })
