# ordenestrabajo/api_views.py

from datetime import datetime, timedelta, time as dtime
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.db.models import Max

from autenticacion.models import Empleado
from talleres.models import Taller
from vehiculos.models import Vehiculo
from autenticacion.roles import supervisor_only
from .models import OrdenTrabajo
import re


ACTIVE_STATES = ["Pendiente", "En Proceso", "En Taller"]


# ==========================================================
# 📅 API Agenda
# ==========================================================
@login_required
@require_GET
def api_agenda_slots(request):
    fecha_str = request.GET.get("fecha")
    taller_id = request.GET.get("taller_id")

    if not fecha_str or not taller_id:
        return JsonResponse({"success": False, "message": "Debe indicar fecha y taller."}, status=400)

    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"success": False, "message": "Fecha inválida."}, status=400)

    try:
        taller_id_int = int(taller_id)
    except ValueError:
        return JsonResponse({"success": False, "message": "Taller inválido."}, status=400)

    if not Taller.objects.filter(taller_id=taller_id_int).exists():
        return JsonResponse({"success": False, "message": "Taller no encontrado."}, status=404)

    start_dt = datetime.combine(fecha, dtime(9, 0))
    end_dt = datetime.combine(fecha, dtime(18, 0))

    ots = OrdenTrabajo.objects.filter(
        fecha_ingreso=fecha,
        taller_id=taller_id_int,
        estado__in=ACTIVE_STATES
    ).values_list("hora_ingreso", flat=True)

    ocupados = {h.strftime("%H:%M") for h in ots if h}

    slots = []
    current = start_dt
    while current <= end_dt:
        hora = current.strftime("%H:%M")
        slots.append({"hora": hora, "ocupado": hora in ocupados})
        current += timedelta(minutes=60)

    return JsonResponse({"success": True, "slots": slots})


# ==========================================================
# 📝 API Crear OT
# ==========================================================
@csrf_exempt
@login_required
@require_POST
def api_crear_ingreso(request):

    user = request.user

    empleado = Empleado.objects.select_related("taller").filter(usuario=user.username).first()
    if not empleado:
        return JsonResponse({"success": False, "message": "Empleado no encontrado."}, status=400)

    patente = (request.POST.get("patente") or "").strip().upper()
    fecha_str = request.POST.get("fecha") or ""
    hora_str = request.POST.get("hora") or ""
    taller_id = request.POST.get("taller_id") or ""
    descripcion = (request.POST.get("descripcion") or "").strip()

    if not patente:
        return JsonResponse({"success": False, "message": "La patente es obligatoria."}, status=400)
    if not fecha_str or not hora_str or not taller_id:
        return JsonResponse({"success": False, "message": "Debe indicar fecha, hora y taller."}, status=400)
    
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        hora = datetime.strptime(hora_str, "%H:%M").time()
        taller_id_int = int(taller_id)
    except:
        return JsonResponse({"success": False, "message": "Datos inválidos."}, status=400)
    
    if not re.match(r"^[A-Z0-9]{4,8}$", patente):
        return JsonResponse({
            "success": False,
            "message": "Formato de patente inválido."
    }, status=400)

    vehiculo = Vehiculo.objects.filter(patente=patente).first()
    if not vehiculo:
        return JsonResponse({"success": False, "message": f"No existe el vehículo {patente}."}, status=400)

    taller = Taller.objects.filter(taller_id=taller_id_int).first()
    if not taller:
        return JsonResponse({"success": False, "message": "Taller no encontrado."}, status=404)

    # 🔥 VALIDAR QUE EL EMPLEADO PERTENEZCA AL MISMO TALLER
    if empleado.taller_id != taller_id_int:
        return JsonResponse({
            "success": False,
            "message": "No puedes registrar ingresos en un taller que no es el tuyo."
        }, status=403)


    ot_activa = OrdenTrabajo.objects.filter(
        patente=vehiculo,
        estado__in=ACTIVE_STATES
    ).first()

    if ot_activa:
        return JsonResponse({
            "success": False,
            "message": f"Ya existe una OT activa #{ot_activa.ot_id} para {patente}."
        }, status=409)

    slot_ocupado = OrdenTrabajo.objects.filter(
        fecha_ingreso=fecha,
        hora_ingreso=hora,
        taller_id=taller_id_int,
        estado__in=ACTIVE_STATES
    ).exists()

    if slot_ocupado:
        return JsonResponse({"success": False, "message": "El horario seleccionado ya está ocupado."}, status=409)

    ot = OrdenTrabajo.objects.create(
        fecha_ingreso=fecha,
        hora_ingreso=hora,
        descripcion=descripcion,
        estado="Pendiente",
        patente=vehiculo,
        taller=taller,
        rut=empleado,
        rut_creador=empleado
    )

    vehiculo.estado = "Disponible"  
    vehiculo.ubicacion = taller.nombre
    vehiculo.save()

    return JsonResponse({
        "success": True,
        "ot": {
            "id": ot.ot_id,
            "patente": ot.patente_id,
            "hora": hora.strftime("%H:%M"),
            "taller_id": ot.taller_id,
        }
    }, status=201)

# ==========================================================
# 📋 API Últimas OT cuya última OT esté finalizada + vehículo disponible
# ==========================================================
@login_required
@require_GET
def api_ultimas_ot(request):

    # 1️⃣ Subquery: obtener la última OT por vehículo (patente_id)
    subquery = (
        OrdenTrabajo.objects
        .values("patente_id")
        .annotate(ultima_ot=Max("ot_id"))
        .values_list("ultima_ot", flat=True)
    )

    # 2️⃣ Filtrar últimas OT finalizadas + vehículo disponible
    ots = (
        OrdenTrabajo.objects
        .select_related("patente", "taller")
        .filter(
            ot_id__in=subquery,       # solo la última OT del vehículo
            estado="Finalizado",      # esa OT debe estar finalizada
            patente__estado="Disponible"  # vehículo debe estar disponible
        )
        .order_by("-ot_id")[:15]
    )

    html = render_to_string(
        "partials/tabla_ultimos_ingresos.html",
        {"ots": ots}
    )
    return JsonResponse({"success": True, "html": html})
# ==========================================================
# 🛠 API Asignar OT (Supervisor)
# ==========================================================
@login_required
@supervisor_only
@require_POST
def api_asignar_ot(request):

    ot_id = request.POST.get("ot_id")
    mecanico_rut = request.POST.get("mecanico_rut")
    comentario = (request.POST.get("comentario") or "").strip()

    if not comentario:
        return JsonResponse({"success": False, "message": "Debe ingresar comentario."})

    supervisor = (
        Empleado.objects
        .filter(usuario=request.user.username)
        .select_related("taller")
        .first()
    )

    ot = (
        OrdenTrabajo.objects
        .filter(
            ot_id=ot_id,
            estado="Pendiente",
            taller_id=supervisor.taller.taller_id,
            is_active=True,  # 👈 solo mecánicos activos
        )
        .select_related("patente")
        .first()
    )

    if not ot:
        return JsonResponse({"success": False, "message": "OT no válida para este taller."})

    mec = (
        Empleado.objects
        .filter(
            rut=mecanico_rut,
            cargo="MECANICO",
            taller_id=supervisor.taller.taller_id
        )
        .first()
    )

    if not mec:
        return JsonResponse({"success": False, "message": "Mecánico inválido."})

    ot.estado = "En Taller"
    ot.rut = mec
    ot.descripcion = (ot.descripcion or "") + f"\n[Supervisor {supervisor.usuario}] {comentario}"
    ot.save()

    veh = ot.patente
    veh.estado = "En Taller"
    veh.ubicacion = supervisor.taller.nombre
    veh.save()

    return JsonResponse({"success": True})


# ==========================================================
# 🧰 API — MECÁNICO: vehículos asignados
# GET /api/ordenestrabajo/mecanico/vehiculos/
# ==========================================================
@login_required
@require_GET
def api_mecanico_vehiculos(request):

    empleado = Empleado.objects.filter(usuario=request.user.username).first()
    if not empleado:
        return JsonResponse({"success": False, "message": "Empleado no encontrado."})

    ots = (
        OrdenTrabajo.objects
        .select_related("patente")
        .filter(
            rut=empleado.rut,
            estado__in=["En Taller", "En Proceso", "Pausado"]
        )
        .order_by("-ot_id")
    )

    html = render_to_string(
        "partials/tabla_vehiculos_taller.html",
        {"ots": ots}
    )

    return JsonResponse({"success": True, "html": html})

# ==========================================================
# 🧰 API — SUPERVISOR: vehículos PENDIENTES de su taller
# GET /api/ordenestrabajo/supervisor/vehiculos/
# ==========================================================
@login_required
@supervisor_only
@require_GET
def api_supervisor_vehiculos(request):

    supervisor = (
        Empleado.objects
        .select_related("taller")
        .filter(usuario=request.user.username)
        .first()
    )

    if not supervisor or not supervisor.taller_id:
        return JsonResponse({
            "success": False,
            "message": "No se pudo determinar tu taller.",
            "html": "<tr><td colspan='6' class='text-center text-danger'>No se pudo determinar tu taller.</td></tr>",
        })

    # Solo OTs PENDIENTES de este taller (las que se muestran en Asignación)
    ots = (
        OrdenTrabajo.objects
        .select_related("patente", "taller", "rut")
        .filter(
            taller_id=supervisor.taller_id,
            estado="Pendiente",
        )
        .order_by("fecha_ingreso", "hora_ingreso")
    )

    html = render_to_string(
        "partials/tabla_asignacion_pendientes.html",
        {"ots": ots},
    )

    return JsonResponse({"success": True, "html": html})
