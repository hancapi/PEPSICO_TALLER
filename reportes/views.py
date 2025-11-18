# reportes/views.py
from django.db.models import Avg, F, ExpressionWrapper, DurationField
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from vehiculos.models import Vehiculo
from talleres.models import Taller
from ordenestrabajo.models import OrdenTrabajo
from autenticacion.models import Empleado
from autenticacion.roles import supervisor_only

from datetime import datetime, timedelta


# ==============================================================
# 🔹 Página HTML
# ==============================================================
@login_required(login_url='/inicio-sesion/')
@supervisor_only
def reportes_page(request):
    return render(request, "reportes.html", {
        "menu_active": "reportes"
    })


# ==============================================================
# 🟦 Helper: parseo fechas
# ==============================================================
def _parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except:
        return None


def _date_range(request):
    today = datetime.today().date()

    dfrom = _parse_date(request.GET.get("from") or "") or (today - timedelta(days=30))
    dto   = _parse_date(request.GET.get("to") or "") or today

    if dfrom > dto:
        dfrom, dto = dto, dfrom

    return dfrom, dto


# ==============================================================
# 🟦 NUEVA API: SUMMARY (lo que reportes.js espera)
# ==============================================================
@login_required
@supervisor_only
def api_summary(request):
    dfrom, dto = _date_range(request)

    total_vehiculos = Vehiculo.objects.count()
    en_taller = Vehiculo.objects.filter(estado="En Taller").count()

    ordenes_activas = OrdenTrabajo.objects.filter(
        fecha_ingreso__range=(dfrom, dto),
        estado__in=["Pendiente", "En Proceso"]
    ).count()

    empleados_activos = Empleado.objects.filter(is_active=True).count()

    return JsonResponse({
        "success": True,
        "kpis": {
            "vehiculos_totales": total_vehiculos,
            "en_taller": en_taller,
            "en_proceso": ordenes_activas,
            "empleados_activos": empleados_activos,
        }
    })


# ==============================================================
# 🟦 NUEVA API: Lista de OTs filtrada (lo que reportes.js usa)
# ==============================================================
@login_required
@supervisor_only
def api_ots(request):
    dfrom, dto = _date_range(request)

    patente = (request.GET.get("patente") or "").strip().upper()
    estado  = (request.GET.get("estado") or "").strip()
    taller  = (request.GET.get("taller_id") or "").strip()
    creador = (request.GET.get("rut_creador") or "").strip()

    qs = OrdenTrabajo.objects.filter(
        fecha_ingreso__range=(dfrom, dto)
    ).select_related("patente", "taller", "rut_creador")

    if patente:
        qs = qs.filter(patente_id=patente)

    if estado:
        qs = qs.filter(estado=estado)

    if taller:
        if taller.isdigit():
            qs = qs.filter(taller_id=int(taller))
        else:
            ids = list(Taller.objects.filter(nombre__icontains=taller)
                                    .values_list("taller_id", flat=True))
            qs = qs.filter(taller_id__in=ids or [-1])

    if creador:
        qs = qs.filter(rut_creador__rut=creador)

    items = [{
        "id": ot.ot_id,
        "fecha": ot.fecha_ingreso.isoformat(),
        "hora": ot.hora_ingreso.strftime("%H:%M") if ot.hora_ingreso else None,
        "patente": ot.patente_id,
        "taller_nombre": ot.taller.nombre if ot.taller else "",
        "estado": ot.estado,
        "rut_creador": getattr(ot.rut_creador, "rut", "")
    } for ot in qs.order_by("-fecha_ingreso", "-hora_ingreso")]

    return JsonResponse({"success": True, "items": items})


# ==============================================================
# 🔹 API: Resumen Global (ya existía)
# ==============================================================
@login_required(login_url='/inicio-sesion/')
@supervisor_only
def api_resumen_global(request):

    total_vehiculos = Vehiculo.objects.count()
    en_taller = Vehiculo.objects.filter(estado="En Taller").count()

    ordenes_activas = OrdenTrabajo.objects.filter(
        estado__in=["Pendiente", "En Proceso"]
    ).count()

    empleados_activos = Empleado.objects.filter(is_active=True).count()

    return JsonResponse({
        "success": True,
        "data": {
            "vehiculos_totales": total_vehiculos,
            "vehiculos_en_taller": en_taller,
            "ordenes_activas": ordenes_activas,
            "empleados_activos": empleados_activos,
        }
    })


# ==============================================================
# 🔹 API: Resumen por Taller
# ==============================================================
@login_required(login_url='/inicio-sesion/')
@supervisor_only
def api_resumen_talleres(request):

    talleres = []

    for t in Taller.objects.all():
        vehiculos_total = Vehiculo.objects.filter(ubicacion=t.nombre).count()

        talleres.append({
            "taller_id": t.taller_id,
            "nombre": t.nombre,
            "ubicacion": t.ubicacion,
            "vehiculos_total": vehiculos_total,
            "ots_pendientes": OrdenTrabajo.objects.filter(taller=t, estado="Pendiente").count(),
            "ots_en_proceso": OrdenTrabajo.objects.filter(taller=t, estado="En Proceso").count(),
            "ots_finalizadas": OrdenTrabajo.objects.filter(taller=t, estado="Finalizado").count(),
        })

    return JsonResponse({"success": True, "items": talleres})


# ==============================================================
# 🔹 API: Promedio de tiempos
# ==============================================================
@login_required(login_url='/inicio-sesion/')
@supervisor_only
def api_tiempos_promedio(request):

    qs = OrdenTrabajo.objects.exclude(fecha_salida__isnull=True)

    qs = qs.annotate(
        duracion=ExpressionWrapper(
            F("fecha_salida") - F("fecha_ingreso"),
            output_field=DurationField()
        )
    )

    global_avg = qs.aggregate(promedio=Avg("duracion"))["promedio"]

    talleres = {}
    for t in Taller.objects.all():
        dur = qs.filter(taller=t).aggregate(promedio=Avg("duracion"))["promedio"]
        talleres[t.taller_id] = {
            "taller": t.nombre,
            "promedio_dias": round(dur.total_seconds() / 86400, 2) if dur else None
        }

    return JsonResponse({
        "success": True,
        "global_promedio_dias": round(global_avg.total_seconds() / 86400, 2) if global_avg else None,
        "por_taller": talleres
    })
