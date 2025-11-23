# ordenestrabajo/api_views.py
from datetime import datetime, timedelta, time as dtime
import logging
import re

from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from autenticacion.models import Empleado
from autenticacion.roles import supervisor_only
from talleres.models import Taller
from vehiculos.models import Vehiculo
from .models import OrdenTrabajo, SolicitudIngresoVehiculo


logger = logging.getLogger(__name__)

# Estados considerados como "activos" para una OT (se muestran en Registro Taller
# y bloquean nuevos horarios para el mismo vehículo/hora/taller).
ACTIVE_STATES = ["Pendiente", "Recibida", "En Taller", "En Proceso", "Pausado"]


# ==========================================================
# HELPERS COMPARTIDOS
# ==========================================================
def _get_supervisor(request):
    """
    Devuelve el Empleado que corresponde al usuario autenticado
    con su taller pre-cargado (select_related('taller')).
    """
    return (
        Empleado.objects
        .select_related("taller")
        .filter(usuario=request.user.username)
        .first()
    )


def _ot_activa_para_vehiculo(vehiculo):
    """
    Retorna la OT activa más reciente para un vehículo, si existe.
    Una OT se considera activa si su estado está en ACTIVE_STATES.
    """
    return (
        OrdenTrabajo.objects
        .filter(patente=vehiculo, estado__in=ACTIVE_STATES)
        .order_by("-fecha_ingreso", "-hora_ingreso")
        .first()
    )


def _get_mecanico_en_taller(mecanico_rut, taller_id):
    """
    Devuelve el mecánico activo para el RUT indicado dentro del taller dado,
    o None si no existe / no cumple condiciones.
    """
    return (
        Empleado.objects
        .filter(
            rut=mecanico_rut,
            cargo="MECANICO",
            taller_id=taller_id,
            is_active=True,
        )
        .first()
    )


# ==========================================================
# 📅 API Agenda (slots por hora en un día/taller)
# GET /api/ordenestrabajo/agenda/slots/
# ==========================================================
@login_required
@require_GET
def api_agenda_slots(request):
    fecha_str = request.GET.get("fecha")
    taller_id = request.GET.get("taller_id")

    if not fecha_str or not taller_id:
        return JsonResponse(
            {"success": False, "message": "Debe indicar fecha y taller."},
            status=400,
        )

    # Parseo de fecha
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse(
            {"success": False, "message": "Fecha inválida."},
            status=400,
        )

    # Parseo de ID de taller
    try:
        taller_id_int = int(taller_id)
    except ValueError:
        return JsonResponse(
            {"success": False, "message": "Taller inválido."},
            status=400,
        )

    if not Taller.objects.filter(taller_id=taller_id_int).exists():
        return JsonResponse(
            {"success": False, "message": "Taller no encontrado."},
            status=404,
        )

    # Rango horario fijo 09:00–18:00
    start_dt = datetime.combine(fecha, dtime(9, 0))
    end_dt = datetime.combine(fecha, dtime(18, 0))

    # Horarios ya ocupados por OTs activas
    ots = (
        OrdenTrabajo.objects
        .filter(
            fecha_ingreso=fecha,
            taller_id=taller_id_int,
            estado__in=ACTIVE_STATES,
        )
        .values_list("hora_ingreso", flat=True)
    )

    ocupados = {h.strftime("%H:%M") for h in ots if h}

    # Generar slots de 1 hora
    slots = []
    current = start_dt
    while current <= end_dt:
        hora = current.strftime("%H:%M")
        slots.append({"hora": hora, "ocupado": hora in ocupados})
        current += timedelta(minutes=60)

    return JsonResponse({"success": True, "slots": slots})


# ==========================================================
# 📝 API Crear Solicitud de Ingreso (NO crea OT)
# POST /api/ordenestrabajo/ingresos/create/
# ==========================================================
@csrf_exempt
@login_required
@require_POST
def api_crear_ingreso(request):
    """
    Crea una solicitud de ingreso de vehículo al taller.
    - El chofer define patente, fecha y taller.
    - NO se crea OT en esta etapa.
    - NO se modifica el estado del vehículo.
    """
    user = request.user

    empleado = (
        Empleado.objects
        .select_related("taller")
        .filter(usuario=user.username)
        .first()
    )
    if not empleado:
        return JsonResponse(
            {"success": False, "message": "Empleado no encontrado."},
            status=400,
        )

    patente = (request.POST.get("patente") or "").strip().upper()
    fecha_str = request.POST.get("fecha") or ""
    taller_id = request.POST.get("taller_id") or ""
    descripcion = (request.POST.get("descripcion") or "").strip()

    # Validaciones básicas
    if not patente:
        return JsonResponse(
            {"success": False, "message": "La patente es obligatoria."},
            status=400,
        )
    if not fecha_str or not taller_id:
        return JsonResponse(
            {"success": False, "message": "Debe indicar fecha y taller."},
            status=400,
        )

    # Parseo de fecha y taller
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        taller_id_int = int(taller_id)
    except Exception:
        return JsonResponse(
            {"success": False, "message": "Datos inválidos."},
            status=400,
        )

    # Formato de patente
    if not re.match(r"^[A-Z0-9]{4,8}$", patente):
        return JsonResponse(
            {"success": False, "message": "Formato de patente inválido."},
            status=400,
        )

    vehiculo = Vehiculo.objects.filter(patente=patente).first()
    if not vehiculo:
        return JsonResponse(
            {"success": False, "message": f"No existe el vehículo {patente}."},
            status=400,
        )

    taller = Taller.objects.filter(taller_id=taller_id_int).first()
    if not taller:
        return JsonResponse(
            {"success": False, "message": "Taller no encontrado."},
            status=404,
        )

    # Validar que el empleado pertenezca al mismo taller
    if empleado.taller_id != taller_id_int:
        return JsonResponse(
            {
                "success": False,
                "message": "No puedes registrar ingresos en un taller que no es el tuyo.",
            },
            status=403,
        )

    # Validar que NO haya OT activa para ese vehículo
    ot_activa = _ot_activa_para_vehiculo(vehiculo)
    if ot_activa:
        logger.warning(
            "Intento de crear solicitud con OT activa. Patente=%s OT=%s Usuario=%s",
            vehiculo.patente,
            ot_activa.ot_id,
            request.user.username,
        )
        return JsonResponse(
            {
                "success": False,
                "message": f"Ya existe una OT activa #{ot_activa.ot_id} para {vehiculo.patente}.",
            },
            status=409,
        )

    # Crear la SOLICITUD (no la OT)
    solicitud = SolicitudIngresoVehiculo.objects.create(
        vehiculo=vehiculo,
        chofer=empleado,
        taller=taller,
        fecha_solicitada=fecha,
        descripcion=descripcion,
        # estado por defecto: PENDIENTE
    )

    # No se toca vehiculo.estado ni ubicacion aquí.
    # Eso ocurrirá cuando el supervisor apruebe y genere la OT.

    return JsonResponse(
        {
            "success": True,
            "solicitud_id": solicitud.id,
            "message": "Solicitud de ingreso registrada correctamente.",
        },
        status=201,
    )


# ==========================================================
# 📋 API Últimas OT finalizadas con vehículo disponible
# GET /api/ordenestrabajo/ultimas/
# ==========================================================
@login_required
@require_GET
def api_ultimas_ot(request):
    """
    Devuelve las últimas OTs finalizadas para cada vehículo
    cuya unidad se encuentra actualmente disponible.
    """
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
            ot_id__in=subquery,            # solo la última OT del vehículo
            estado="Finalizado",           # esa OT debe estar finalizada
            patente__estado="Disponible",  # vehículo debe estar disponible
        )
        .order_by("-ot_id")[:15]
    )

    html = render_to_string(
        "partials/tabla_ultimos_ingresos.html",
        {"ots": ots},
    )
    return JsonResponse({"success": True, "html": html})


# ==========================================================
# 🛠 API Asignar OT (Supervisor) — FLUJO LEGACY
# POST /api/ordenestrabajo/asignar/
# ==========================================================
@login_required
@supervisor_only
@require_POST
def api_asignar_ot(request):
    """
    Flujo antiguo: asigna mecánico a una OT ya pendiente
    y la pasa a estado "En Taller".
    """
    ot_id = request.POST.get("ot_id")
    mecanico_rut = request.POST.get("mecanico_rut")
    comentario = (request.POST.get("comentario") or "").strip()

    if not comentario:
        return JsonResponse(
            {"success": False, "message": "Debe ingresar comentario."}
        )

    supervisor = _get_supervisor(request)
    if not supervisor or not supervisor.taller:
        return JsonResponse(
            {"success": False, "message": "No se pudo determinar tu taller."}
        )

    ot = (
        OrdenTrabajo.objects
        .filter(
            ot_id=ot_id,
            estado="Pendiente",
            taller_id=supervisor.taller.taller_id,
        )
        .select_related("patente")
        .first()
    )
    if not ot:
        return JsonResponse(
            {"success": False, "message": "OT no válida para este taller."}
        )

    mec = _get_mecanico_en_taller(mecanico_rut, supervisor.taller.taller_id)
    if not mec:
        return JsonResponse(
            {"success": False, "message": "Mecánico inválido."}
        )

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
        return JsonResponse(
            {"success": False, "message": "Empleado no encontrado."}
        )

    ots = (
        OrdenTrabajo.objects
        .select_related("patente")
        .filter(
            rut=empleado.rut,
            estado__in=ACTIVE_STATES,
        )
        .order_by("-ot_id")
    )

    html = render_to_string(
        "partials/tabla_vehiculos_taller.html",
        {"ots": ots},
    )

    return JsonResponse({"success": True, "html": html})


# ==========================================================
# 🧰 API — SUPERVISOR: vehículos EN TALLER de su taller
# GET /api/ordenestrabajo/supervisor/vehiculos/
# ==========================================================
@login_required
@supervisor_only
@require_GET
def api_supervisor_vehiculos(request):
    supervisor = _get_supervisor(request)

    if not supervisor or not supervisor.taller_id:
        return JsonResponse(
            {
                "success": False,
                "message": "No se pudo determinar tu taller.",
                "html": "<div class='alert alert-danger'>No se pudo determinar tu taller.</div>",
            }
        )

    ots = (
        OrdenTrabajo.objects
        .select_related("patente", "taller", "rut")
        .filter(
            taller_id=supervisor.taller_id,
            estado__in=ACTIVE_STATES,
        )
        .order_by("-fecha_ingreso", "-hora_ingreso")
    )

    html = render_to_string(
        "partials/tabla_vehiculos_taller.html",
        {"ots": ots},
    )

    return JsonResponse({"success": True, "html": html})


# ==========================================================
# 🧰 API — SUPERVISOR: OTs PENDIENTES de su taller (LEGACY)
# GET /api/ordenestrabajo/supervisor/pendientes/
# ==========================================================
@login_required
@supervisor_only
@require_GET
def api_supervisor_pendientes(request):
    """
    Flujo antiguo: lista OTs en estado Pendiente
    del taller del supervisor.
    """
    supervisor = _get_supervisor(request)

    if not supervisor or not supervisor.taller_id:
        return JsonResponse(
            {
                "success": False,
                "message": "No se pudo determinar tu taller.",
                "html": "<tr><td colspan='6' class='text-center text-danger'>No se pudo determinar tu taller.</td></tr>",
            }
        )

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


# ==========================================================
# 🧰 API — SUPERVISOR: Solicitudes de ingreso PENDIENTES
# GET /api/ordenestrabajo/supervisor/solicitudes/
# ==========================================================
@login_required
@supervisor_only
@require_GET
def api_supervisor_solicitudes(request):
    """
    Devuelve las solicitudes de ingreso PENDIENTES
    del taller del supervisor.
    """
    supervisor = _get_supervisor(request)

    if not supervisor or not supervisor.taller_id:
        return JsonResponse(
            {
                "success": False,
                "message": "No se pudo determinar tu taller.",
                "html": "<tr><td colspan='7' class='text-center text-danger'>No se pudo determinar tu taller.</td></tr>",
            }
        )

    solicitudes = (
        SolicitudIngresoVehiculo.objects
        .select_related("vehiculo", "chofer", "taller")
        .filter(
            taller_id=supervisor.taller_id,
            estado="PENDIENTE",
        )
        .order_by("fecha_solicitada", "creado_en")
    )

    html = render_to_string(
        "partials/tabla_solicitudes_ingreso.html",
        {"solicitudes": solicitudes},
    )

    return JsonResponse({"success": True, "html": html})


# ==========================================================
# 🧰 API — SUPERVISOR: Aprobar solicitud y crear OT
# POST /api/ordenestrabajo/supervisor/solicitud/aprobar/
# ==========================================================
@login_required
@supervisor_only
@require_POST
def api_supervisor_aprobar_solicitud(request):
    """
    Aprueba una solicitud de ingreso, programa fecha/hora de recepción,
    asigna mecánico y crea la OT correspondiente.

    El módulo/pasillo seleccionado se almacena como parte de la descripción
    de la OT, manteniendo la tabla ordenestrabajo sin cambios de esquema.
    """
    solicitud_id = request.POST.get("solicitud_id")
    mecanico_rut = request.POST.get("mecanico_rut")
    comentario = (request.POST.get("comentario") or "").strip()
    fecha_str = request.POST.get("fecha") or ""
    hora_str = request.POST.get("hora") or ""
    modulo = (request.POST.get("modulo") or "").strip()

    if not comentario:
        return JsonResponse(
            {"success": False, "message": "Debe ingresar comentario."}
        )

    if not fecha_str or not hora_str:
        return JsonResponse(
            {"success": False, "message": "Debe indicar fecha y hora de ingreso."}
        )

    if not modulo:
        return JsonResponse(
            {"success": False, "message": "Debe seleccionar un módulo/pasillo del taller."}
        )

    supervisor = _get_supervisor(request)
    if not supervisor or not supervisor.taller_id:
        return JsonResponse(
            {"success": False, "message": "No se pudo determinar tu taller."}
        )

    # Parseo de fecha/hora
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        hora = datetime.strptime(hora_str, "%H:%M").time()
    except Exception:
        return JsonResponse(
            {"success": False, "message": "Fecha u hora inválidas."}
        )

    # Solicitud pendiente
    solicitud = (
        SolicitudIngresoVehiculo.objects
        .select_related("vehiculo", "chofer", "taller")
        .filter(id=solicitud_id, estado="PENDIENTE")
        .first()
    )
    if not solicitud:
        return JsonResponse(
            {"success": False, "message": "Solicitud no válida."}
        )

    if solicitud.taller_id != supervisor.taller_id:
        return JsonResponse(
            {"success": False, "message": "La solicitud no pertenece a tu taller."}
        )

    # Validar mecánico
    mec = _get_mecanico_en_taller(mecanico_rut, supervisor.taller_id)
    if not mec:
        return JsonResponse(
            {"success": False, "message": "Mecánico inválido."}
        )

    vehiculo = solicitud.vehiculo

    # Regla de negocio: no permitir OT activa para ese vehículo
    ot_activa = _ot_activa_para_vehiculo(vehiculo)
    if ot_activa:
        logger.warning(
            "Intento de aprobar solicitud con OT activa. Patente=%s OT=%s Supervisor=%s",
            vehiculo.patente,
            ot_activa.ot_id,
            request.user.username,
        )
        return JsonResponse(
            {
                "success": False,
                "message": f"Ya existe una OT activa #{ot_activa.ot_id} para {vehiculo.patente}.",
            },
            status=409,
        )

    # Evitar doble horario en mismo taller
    slot_ocupado = (
        OrdenTrabajo.objects
        .filter(
            fecha_ingreso=fecha,
            hora_ingreso=hora,
            taller_id=supervisor.taller_id,
            estado__in=ACTIVE_STATES,
        )
        .exists()
    )
    if slot_ocupado:
        return JsonResponse(
            {
                "success": False,
                "message": "El horario seleccionado ya está ocupado.",
            },
            status=409,
        )

    # Armar descripción final incorporando el módulo/pasillo
    descripcion_ot = f"[Módulo: {modulo}] {comentario}"

    # Crear OT
    ot = OrdenTrabajo.objects.create(
        fecha_ingreso=fecha,
        hora_ingreso=hora,
        descripcion=descripcion_ot,
        estado="Pendiente",
        patente=vehiculo,
        taller=solicitud.taller,
        rut=mec,
        rut_creador=supervisor,
    )

    # Marcar solicitud como aprobada
    solicitud.estado = "APROBADA"
    solicitud.save()

    return JsonResponse(
        {
            "success": True,
            "ot_id": ot.ot_id,
        }
    )
