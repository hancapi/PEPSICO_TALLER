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
# y bloquean nuevos horarios para el mismo vehículo/hora/recinto).
ACTIVE_STATES = ["Pendiente", "Recibida", "En Taller", "En Proceso", "Pausado"]


# ==========================================================
# HELPERS COMPARTIDOS
# ==========================================================
def _get_supervisor(request):
    """
    Devuelve el Empleado que corresponde al usuario autenticado
    con su RECINTO pre-cargado (select_related('recinto')).
    """
    return (
        Empleado.objects
        .select_related("recinto")
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


def _get_mecanico_en_recinto(mecanico_rut, recinto_id):
    """
    Devuelve el mecánico activo para el RUT indicado dentro del RECINTO dado,
    o None si no existe / no cumple condiciones.
    """
    return (
        Empleado.objects
        .filter(
            rut=mecanico_rut,
            cargo="MECANICO",
            recinto_id=recinto_id,
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

    taller = Taller.objects.filter(taller_id=taller_id_int).first()
    if not taller:
        return JsonResponse(
            {"success": False, "message": "Taller no encontrado."},
            status=404,
        )

    # Usamos el RECINTO del taller para buscar las OTs de ese lugar
    recinto_id = taller.recinto_id

    # Rango horario fijo 09:00–18:00
    start_dt = datetime.combine(fecha, dtime(9, 0))
    end_dt = datetime.combine(fecha, dtime(18, 0))

    # Horarios ya ocupados por OTs activas en ese RECINTO
    ots = (
        OrdenTrabajo.objects
        .filter(
            fecha_ingreso=fecha,
            recinto_id=recinto_id,
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
    - El chofer define patente, fecha y taller (andén).
    - NO se crea OT en esta etapa.
    - NO se modifica el estado del vehículo.
    """
    user = request.user

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

    # Validar que el empleado pertenezca al mismo RECINTO del taller
    if empleado.recinto_id != taller.recinto_id:
        return JsonResponse(
            {
                "success": False,
                "message": "No puedes registrar ingresos en un taller de otro recinto.",
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

    # Si por pruebas anteriores el vehículo quedó "En Taller" pero ahora no tiene OT activa,
    # lo devolvemos a "Disponible".
    if vehiculo.estado == "En Taller":
        vehiculo.estado = "Disponible"
        vehiculo.save()

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
        .select_related("patente", "recinto")
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
    if not supervisor or not supervisor.recinto_id:
        return JsonResponse(
            {"success": False, "message": "No se pudo determinar tu recinto."}
        )

    ot = (
        OrdenTrabajo.objects
        .filter(
            ot_id=ot_id,
            estado="Pendiente",
            recinto_id=supervisor.recinto_id,
        )
        .select_related("patente", "recinto")
        .first()
    )
    if not ot:
        return JsonResponse(
            {"success": False, "message": "OT no válida para tu recinto."}
        )

    mec = _get_mecanico_en_recinto(mecanico_rut, supervisor.recinto_id)
    if not mec:
        return JsonResponse(
            {"success": False, "message": "Mecánico inválido."}
        )

    # 🔹 nombre y cargo legible del supervisor
    display_nombre = supervisor.nombre or supervisor.usuario
    if supervisor.cargo:
        cargo_raw = supervisor.cargo.upper()
        if cargo_raw == "SUPERVISOR":
            cargo_label = "Supervisor"
        elif cargo_raw == "MECANICO":
            cargo_label = "Mecánico"
        else:
            cargo_label = supervisor.cargo.title()
    else:
        cargo_label = "Usuario"

    autor_tag = f"[{cargo_label} {display_nombre}]"

    ot.estado = "En Taller"
    ot.rut = mec

    base = (ot.descripcion or "").rstrip()
    prefix = "\n" if base else ""
    ot.descripcion = f"{base}{prefix}{autor_tag} {comentario}"

    ot.save()

    veh = ot.patente
    veh.estado = "En Taller"
    # Ubicación: nombre del recinto del supervisor
    if supervisor.recinto:
        veh.ubicacion = supervisor.recinto.nombre
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
        .select_related("patente", "recinto")
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
# 🧰 API — SUPERVISOR: vehículos EN TALLER de su recinto
# GET /api/ordenestrabajo/supervisor/vehiculos/
# ==========================================================
@login_required
@supervisor_only
@require_GET
def api_supervisor_vehiculos(request):
    supervisor = _get_supervisor(request)

    if not supervisor or not supervisor.recinto_id:
        return JsonResponse(
            {
                "success": False,
                "message": "No se pudo determinar tu recinto.",
                "html": "<div class='alert alert-danger'>No se pudo determinar tu recinto.</div>",
            }
        )

    ots = (
        OrdenTrabajo.objects
        .select_related("patente", "recinto", "rut")
        .filter(
            recinto_id=supervisor.recinto_id,
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
# 🧰 API — SUPERVISOR: OTs PENDIENTES de su recinto (LEGACY)
# GET /api/ordenestrabajo/supervisor/pendientes/
# ==========================================================
@login_required
@supervisor_only
@require_GET
def api_supervisor_pendientes(request):
    """
    Flujo antiguo: lista OTs en estado Pendiente
    del recinto del supervisor.
    """
    supervisor = _get_supervisor(request)

    if not supervisor or not supervisor.recinto_id:
        return JsonResponse(
            {
                "success": False,
                "message": "No se pudo determinar tu recinto.",
                "html": "<tr><td colspan='6' class='text-center text-danger'>No se pudo determinar tu recinto.</td></tr>",
            }
        )

    ots = (
        OrdenTrabajo.objects
        .select_related("patente", "recinto", "rut")
        .filter(
            recinto_id=supervisor.recinto_id,
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
    de los talleres del recinto del supervisor.
    """
    supervisor = _get_supervisor(request)

    if not supervisor or not supervisor.recinto_id:
        return JsonResponse(
            {
                "success": False,
                "message": "No se pudo determinar tu recinto.",
                "html": "<tr><td colspan='7' class='text-center text-danger'>No se pudo determinar tu recinto.</td></tr>",
            }
        )

    solicitudes = (
        SolicitudIngresoVehiculo.objects
        .select_related("vehiculo", "chofer", "taller")
        .filter(
            taller__recinto_id=supervisor.recinto_id,
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
    if not supervisor or not supervisor.recinto_id:
        return JsonResponse(
            {"success": False, "message": "No se pudo determinar tu recinto."}
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

    # La solicitud debe pertenecer a un taller dentro del RECINTO del supervisor
    if solicitud.taller.recinto_id != supervisor.recinto_id:
        return JsonResponse(
            {"success": False, "message": "La solicitud no pertenece a tu recinto."}
        )

    # Validar mecánico en el mismo recinto
    mec = _get_mecanico_en_recinto(mecanico_rut, supervisor.recinto_id)
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

    # Evitar doble horario en mismo RECINTO
    slot_ocupado = (
        OrdenTrabajo.objects
        .filter(
            fecha_ingreso=fecha,
            hora_ingreso=hora,
            recinto_id=supervisor.recinto_id,
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

    # 🔹 nombre y cargo legible del supervisor
    display_nombre = supervisor.nombre or supervisor.usuario
    if supervisor.cargo:
        cargo_raw = supervisor.cargo.upper()
        if cargo_raw == "SUPERVISOR":
            cargo_label = "Supervisor"
        elif cargo_raw == "MECANICO":
            cargo_label = "Mecánico"
        else:
            cargo_label = supervisor.cargo.title()
    else:
        cargo_label = "Usuario"

    autor_tag = f"[{cargo_label} {display_nombre}]"

    # Armar descripción final incorporando AUTOR + MÓDULO/PASILLO
    descripcion_ot = f"{autor_tag} [{modulo}] {comentario}"

    # Crear OT — ahora ligada al RECINTO del supervisor
    ot = OrdenTrabajo.objects.create(
        fecha_ingreso=fecha,
        hora_ingreso=hora,
        descripcion=descripcion_ot,
        estado="Pendiente",
        patente=vehiculo,
        recinto_id=supervisor.recinto_id,
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
