# talleres/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import date

from autenticacion.models import Empleado
from autenticacion.roles import mecanico_or_supervisor
from vehiculos.models import Vehiculo
from ordenestrabajo.models import OrdenTrabajo


def normalize(p):
    return "" if not p else p.replace(".", "").replace("-", "").strip().upper()


@login_required
@mecanico_or_supervisor
def registro_taller_page(request):

    user = request.user

    # Antes: select_related("taller") → ahora usamos "recinto"
    empleado = (
        Empleado.objects
        .select_related("recinto")
        .filter(usuario=user.username)
        .first()
    )

    # modo de vista según cargo
    modo = "mecanico"
    if empleado and empleado.cargo and empleado.cargo.upper() == "SUPERVISOR":
        modo = "supervisor"

    # Antes: empleado.taller → ahora empleado.recinto
    if not empleado or not empleado.recinto:
        return render(request, "registro-taller.html", {
            "menu_active": "registro_taller",
            "error": "No tienes recinto/taller asignado.",
            "empleado": empleado,
            "vehiculos": [],
            "kpis": {"total_vehiculos": 0, "en_taller": 0, "en_proceso": 0},
            "modo": modo,
        })

    # ============================================================
    # POST → actualizar estado de OT
    # ============================================================
    if request.method == "POST":

        patente = normalize(request.POST.get("patente"))
        nuevo_estado = request.POST.get("estado")
        comentario = (request.POST.get("comentario") or "").strip()

        if not patente or not nuevo_estado:
            return JsonResponse({"success": False, "message": "Debe indicar patente y estado."})

        if nuevo_estado == "Finalizado" and comentario == "":
            return JsonResponse({
                "success": False,
                "message": "Debe ingresar un comentario para finalizar la OT."
            })

        veh = Vehiculo.objects.filter(patente=patente).first()
        if not veh:
            return JsonResponse({"success": False, "message": f"No existe el vehículo {patente}."})

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

        estado_actual = ot.estado

        if nuevo_estado not in TRANSICIONES_VALIDAS.get(estado_actual, []):
            return JsonResponse({
                "success": False,
                "message": f"No se puede cambiar de {estado_actual} a {nuevo_estado}."
            })

        ot.estado = nuevo_estado
        ot.descripcion = (ot.descripcion or "") + f"\n[{user.username}] {comentario}"

        if nuevo_estado == "Finalizado":
            ot.fecha_salida = date.today()
            veh.estado = "Disponible"
        else:
            veh.estado = nuevo_estado

        veh.save()
        ot.save()

        return JsonResponse({"success": True, "message": "Estado actualizado correctamente."})

    # ============================================================
    # GET → listar vehículos en taller del mismo RECINTO
    # ============================================================
    ots = (
        OrdenTrabajo.objects
        .select_related("patente")
        .filter(
            recinto=empleado.recinto,
            estado__in=["Pendiente", "En Taller", "En Proceso", "Pausado"],
        )
    )

    patentes = [normalize(ot.patente_id) for ot in ots]
    vehiculos = Vehiculo.objects.filter(patente__in=patentes)

    kpis = {
        "total_vehiculos": vehiculos.count(),
        "en_taller": vehiculos.filter(estado="En Taller").count(),
        "en_proceso": vehiculos.filter(estado="En Proceso").count(),
    }

    return render(request, "registro-taller.html", {
        "menu_active": "registro_taller",
        "empleado": empleado,
        "vehiculos": vehiculos,
        "kpis": kpis,
        "VehiculoModel": Vehiculo,
        "modo": modo,
    })
