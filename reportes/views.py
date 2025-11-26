# reportes/views.py
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, F, ExpressionWrapper, DurationField
from django.http import JsonResponse
from django.shortcuts import render

from vehiculos.models import Vehiculo
from talleres.models import Taller, Recinto
from ordenestrabajo.models import OrdenTrabajo
from autenticacion.models import Empleado
from autenticacion.roles import supervisor_only


# ==============================================================
# 🔹 Página HTML: Dashboard de Reportes (gráficos)
# ==============================================================
@login_required(login_url="/inicio-sesion/")
@supervisor_only
def reportes_page(request):
    return render(request, "reportes.html", {
        "menu_active": "reportes"
    })


# ==============================================================
# 🔹 Página HTML: Reporte de Órdenes de Trabajo (CU07)
#     /reportes/ordenes-trabajo/
# ==============================================================
@login_required(login_url="/inicio-sesion/")
@supervisor_only
def reportes_ot_page(request):
    """
    Página con filtros + tabla de OTs.
    Usa las APIs:
      - /reportes/api/summary/
      - /reportes/api/ots/
    y el JS: static/js/reportes_ot.js

    El combo de "Taller" se alimenta con Recintos,
    porque OrdenTrabajo.recinto es el FK real.
    """
    estados = [choice[0] for choice in OrdenTrabajo.ESTADO_OT_CHOICES]

    # Usamos Recinto en vez de Taller
    talleres = Recinto.objects.all().order_by("nombre")

    return render(request, "reportes_ot.html", {
        "menu_active": "reportes",
        "estados": estados,
        "talleres": talleres,
    })


# ==============================================================
# 🟦 Helper: parseo fechas
# ==============================================================
def _parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def _date_range(request):
    today = datetime.today().date()

    dfrom = _parse_date(request.GET.get("from") or "") or (today - timedelta(days=30))
    dto = _parse_date(request.GET.get("to") or "") or today

    if dfrom > dto:
        dfrom, dto = dto, dfrom

    return dfrom, dto


# ==============================================================
# 🟦 API: SUMMARY (usada por reportes_ot.js)
# ==============================================================
@login_required(login_url="/inicio-sesion/")
@supervisor_only
def api_summary(request):
    dfrom, dto = _date_range(request)

    total_vehiculos = Vehiculo.objects.count()
    en_taller = Vehiculo.objects.filter(estado="En Taller").count()

    ordenes_activas = OrdenTrabajo.objects.filter(
        fecha_ingreso__range=(dfrom, dto),
        estado__in=["Pendiente", "En Proceso"],
    ).count()

    empleados_activos = Empleado.objects.filter(is_active=True).count()

    return JsonResponse({
        "success": True,
        "kpis": {
            "vehiculos_totales": total_vehiculos,
            "en_taller": en_taller,
            "en_proceso": ordenes_activas,
            "empleados_activos": empleados_activos,
        },
    })


# ==============================================================
# 🟦 API: Lista de OTs filtrada (usada por reportes_ot.js)
# ==============================================================
@login_required(login_url="/inicio-sesion/")
@supervisor_only
def api_ots(request):
    dfrom, dto = _date_range(request)

    patente = (request.GET.get("patente") or "").strip().upper()
    estado = (request.GET.get("estado") or "").strip()
    taller = (request.GET.get("taller_id") or "").strip()
    creador = (request.GET.get("rut_creador") or "").strip()

    qs = (
        OrdenTrabajo.objects.filter(fecha_ingreso__range=(dfrom, dto))
        .select_related("patente", "recinto", "rut", "rut_creador")
    )

    if patente:
        qs = qs.filter(patente_id=patente)

    if estado:
        qs = qs.filter(estado=estado)

    if taller:
        if taller.isdigit():
            qs = qs.filter(recinto_id=int(taller))
        else:
            ids = list(
                Recinto.objects.filter(nombre__icontains=taller)
                .values_list("id", flat=True)
            )
            qs = qs.filter(recinto_id__in=ids or [-1])

    if creador:
        qs = qs.filter(rut_creador__rut=creador)

    items = []
    for ot in qs.order_by("-fecha_ingreso", "-hora_ingreso", "-ot_id"):
        # tiempo total en días (si tiene fecha_salida)
        duracion_dias = None
        if ot.fecha_salida and ot.fecha_ingreso:
            duracion_dias = (ot.fecha_salida - ot.fecha_ingreso).days

        items.append({
            "id": ot.ot_id,
            "fecha": ot.fecha_ingreso.isoformat(),
            "hora": ot.hora_ingreso.strftime("%H:%M") if ot.hora_ingreso else "",
            "patente": ot.patente_id,
            "vehiculo": f"{ot.patente.marca} {ot.patente.modelo}" if ot.patente else "",
            "taller_nombre": str(ot.recinto) if ot.recinto else "",
            "estado": ot.estado,
            "rut_mecanico": getattr(ot.rut, "rut", ""),
            "rut_creador": getattr(ot.rut_creador, "rut", ""),
            "fecha_salida": ot.fecha_salida.isoformat() if ot.fecha_salida else "",
            "duracion_dias": duracion_dias,
        })

    return JsonResponse({"success": True, "items": items})


# ==============================================================
# 🔹 API: Resumen Global (dashboard)
#      → /reportes/api/resumen/
# ==============================================================
@login_required(login_url="/inicio-sesion/")
@supervisor_only
def api_resumen_global(request):

    total_vehiculos = Vehiculo.objects.count()
    en_taller = Vehiculo.objects.filter(estado="En Taller").count()

    ordenes_activas = OrdenTrabajo.objects.filter(
        estado__in=["Pendiente", "En Proceso"],
    ).count()

    empleados_activos = Empleado.objects.filter(is_active=True).count()

    return JsonResponse({
        "success": True,
        "data": {
            "vehiculos_totales": total_vehiculos,
            "vehiculos_en_taller": en_taller,
            "ordenes_activas": ordenes_activas,
            "empleados_activos": empleados_activos,
        },
    })


# ==============================================================
# 🔹 API: Resumen por Taller (dashboard)
#      → /reportes/api/talleres/
# ==============================================================
@login_required(login_url="/inicio-sesion/")
@supervisor_only
def api_resumen_talleres(request):
    """
    Devuelve, por cada recinto (que en el dashboard mostramos como "taller"):
      - nombre (string)
      - cantidad de vehículos distintos con OTs en ese recinto
      - cantidad de OTs por estado
    Formato esperado por static/js/reportes.js
    """
    talleres_data = []

    for r in Recinto.objects.all():
        qs_ot = OrdenTrabajo.objects.filter(recinto=r)

        # Vehículos distintos que han tenido OTs en este recinto
        vehiculos_total = qs_ot.values("patente_id").distinct().count()

        talleres_data.append({
            "taller_id": r.pk,
            "nombre": str(r),  # usamos el __str__ del Recinto
            "vehiculos_total": vehiculos_total,
            "ots_pendientes": qs_ot.filter(estado="Pendiente").count(),
            "ots_en_proceso": qs_ot.filter(estado="En Proceso").count(),
            "ots_finalizadas": qs_ot.filter(estado="Finalizado").count(),
        })

    return JsonResponse({"success": True, "items": talleres_data})


# ==============================================================
# 🔹 API: Promedio de tiempos (dashboard)
#      → /reportes/api/tiempos/
# ==============================================================
@login_required(login_url="/inicio-sesion/")
@supervisor_only
def api_tiempos_promedio(request):
    """
    Calcula promedio de duración (en días) de las OTs cerradas,
    global y por recinto. Formato esperado por static/js/reportes.js.
    """

    # Solo OTs que tienen fecha_ingreso y fecha_salida
    qs = OrdenTrabajo.objects.filter(
        fecha_ingreso__isnull=False,
        fecha_salida__isnull=False,
    ).annotate(
        duracion=ExpressionWrapper(
            F("fecha_salida") - F("fecha_ingreso"),
            output_field=DurationField(),
        )
    )

    global_avg = qs.aggregate(promedio=Avg("duracion"))["promedio"]

    talleres = {}
    for r in Recinto.objects.all():
        dur = qs.filter(recinto=r).aggregate(promedio=Avg("duracion"))["promedio"]
        talleres[r.pk] = {
            "taller": str(r),
            "promedio_dias": round(dur.total_seconds() / 86400, 2) if dur else None,
        }

    return JsonResponse({
        "success": True,
        "global_promedio_dias": round(global_avg.total_seconds() / 86400, 2) if global_avg else None,
        "por_taller": talleres,
    })
