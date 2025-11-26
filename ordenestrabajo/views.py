from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST, require_GET

from autenticacion.models import Empleado
from vehiculos.models import Vehiculo
from .models import OrdenTrabajo, Pausa  # Taller ya no es necesario aquí

ACTIVE_STATES = ["Pendiente", "En Proceso", "En Taller"]


# ==========================================================
# 🚫 WHOAMI (para debug)
# ==========================================================
@login_required
def whoami(request):
    return JsonResponse({
        "user": request.user.username,
        "authenticated": True,
        "method": request.method
    })


# ==========================================================
# 🟡 PAUSAS — INICIAR
# ==========================================================
@login_required
@require_POST
def pausa_start(request, ot_id):
    ot = get_object_or_404(OrdenTrabajo, ot_id=ot_id)

    if ot.estado == "Finalizado":
        return JsonResponse(
            {"success": False, "message": "La OT ya está finalizada."},
            status=400
        )

    pausa_activa = Pausa.objects.filter(ot=ot, fin=None).first()
    if pausa_activa:
        return JsonResponse(
            {"success": False, "message": "Ya existe una pausa activa."},
            status=400
        )

    pausa = Pausa.objects.create(
        ot=ot,
        inicio=datetime.now()
    )

    return JsonResponse({
        "success": True,
        "pausa_id": pausa.id,
        "inicio": pausa.inicio.strftime("%Y-%m-%d %H:%M:%S")
    })


# ==========================================================
# 🟢 PAUSAS — DETENER
# ==========================================================
@login_required
@require_POST
def pausa_stop(request, ot_id):
    ot = get_object_or_404(OrdenTrabajo, ot_id=ot_id)

    pausa_activa = Pausa.objects.filter(ot=ot, fin=None).first()
    if not pausa_activa:
        return JsonResponse(
            {"success": False, "message": "No hay pausa activa."},
            status=400
        )

    pausa_activa.fin = datetime.now()
    pausa_activa.save()

    return JsonResponse({
        "success": True,
        "pausa_id": pausa_activa.id,
        "inicio": pausa_activa.inicio.strftime("%Y-%m-%d %H:%M:%S"),
        "fin": pausa_activa.fin.strftime("%Y-%m-%d %H:%M:%S")
    })


# ==========================================================
# 📜 LISTA DE PAUSAS POR OT
# ==========================================================
@login_required
def pausa_list(request, ot_id):
    ot = get_object_or_404(OrdenTrabajo, ot_id=ot_id)
    pausas = Pausa.objects.filter(ot=ot).order_by("-inicio")

    return render(request, "pausas/pausa_list.html", {
        "ot": ot,
        "pausas": pausas,
    })


# ==========================================================
# 📌 API — INGRESOS EN CURSO
# ==========================================================
@login_required
def ingresos_en_curso_api(request):
    user = request.user

    # Antes usábamos taller; ahora trabajamos por RECINTO
    empleado = (
        Empleado.objects
        .select_related("recinto")
        .filter(usuario=user.username)
        .first()
    )

    if not empleado:
        return JsonResponse(
            {"success": False, "message": "Empleado no encontrado."},
            status=400,
        )

    if not empleado.recinto_id:
        return JsonResponse(
            {"success": False, "message": "Empleado sin recinto asignado."},
            status=400,
        )

    ots = (
        OrdenTrabajo.objects
        .filter(
            recinto_id=empleado.recinto_id,
            estado__in=ACTIVE_STATES,
        )
        .order_by("-fecha_ingreso", "-hora_ingreso")
    )

    data = [
        {
            "ot_id": ot.ot_id,
            "patente": ot.patente_id,
            "fecha_ingreso": ot.fecha_ingreso.strftime("%Y-%m-%d"),
            "hora_ingreso": ot.hora_ingreso.strftime("%H:%M") if ot.hora_ingreso else "-",
            "estado": ot.estado,
        }
        for ot in ots
    ]

    return JsonResponse({"success": True, "ordenes": data})


# ==========================================================
# 🔴 FINALIZAR OT
# ==========================================================
@login_required
@require_POST
def ingreso_finalizar_api(request, ot_id):
    ot = get_object_or_404(OrdenTrabajo, ot_id=ot_id)

    if ot.estado == "Finalizado":
        return JsonResponse(
            {"success": False, "message": "La OT ya está finalizada."},
            status=400
        )

    ot.estado = "Finalizado"
    ot.save()

    if ot.patente:
        ot.patente.estado = "Disponible"
        ot.patente.save()

    return JsonResponse({"success": True})


# ==========================================================
# ❌ CANCELAR OT
# ==========================================================
@login_required
@require_POST
def ingreso_cancelar_api(request, ot_id):
    ot = get_object_or_404(OrdenTrabajo, ot_id=ot_id)

    if ot.estado == "Finalizado":
        return JsonResponse(
            {"success": False, "message": "No se puede cancelar una OT finalizada."},
            status=400
        )

    ot.estado = "Cancelado"
    ot.save()

    if ot.patente:
        ot.patente.estado = "Disponible"
        ot.patente.save()

    return JsonResponse({"success": True})
