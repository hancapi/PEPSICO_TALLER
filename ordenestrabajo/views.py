import json
import logging
from datetime import datetime, time, timedelta

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser

from vehiculos.models import Vehiculo
from talleres.models import Taller
from autenticacion.models import Empleado
from .models import OrdenTrabajo, Pausa

logger = logging.getLogger(__name__)

# ======== Configuración de agenda (MVP) ========
SLOT_MINUTES = 30
JORNADA_INICIO = time(8, 0)   # 08:00
JORNADA_FIN    = time(18, 0)  # 18:00

# Estados operativos
ESTADOS_EN_CURSO = ('Pendiente', 'En Proceso')
ESTADO_CANCELADO = 'Cancelado'  # texto libre compatible con tu esquema

# ---------- Helpers ----------
def _get_ot_or_404(ot_id: int):
    try:
        return OrdenTrabajo.objects.get(pk=ot_id)
    except OrdenTrabajo.DoesNotExist:
        return None

def _gen_slots_para_fecha(fecha: datetime.date):
    """Genera tuplas (HH:MM, time_obj) cada SLOT_MINUTES, dentro de la jornada."""
    slots = []
    cur = datetime.combine(fecha, JORNADA_INICIO)
    end = datetime.combine(fecha, JORNADA_FIN)
    while cur < end:
        slots.append((cur.strftime('%H:%M'), cur.time()))
        cur = cur + timedelta(minutes=SLOT_MINUTES)
    return slots

def _ensure_admin_for_taller(taller: Taller) -> Empleado:
    """
    Garantiza que exista un empleado 'admin' en el taller dado.
    Retorna el Empleado admin (exista o recién creado).
    """
    emp = Empleado.objects.filter(taller_id=taller.taller_id).first()
    if emp:
        return emp

    admin_rut = '11.111.111-1'
    admin, _ = Empleado.objects.get_or_create(
        rut=admin_rut,
        defaults=dict(
            nombre='Admin Taller',
            cargo='Supervisor',
            region='RM',
            horario='08:00-17:00',
            disponibilidad=True,
            password='1234',        # MVP (si usarás login con este, pon hash real)
            usuario='admin',
            taller_id=taller.taller_id,
            is_staff=True,
            is_active=True,
            is_superuser=True,
        )
    )
    return admin

def _resolve_responsable(payload, taller: Taller):
    """
    Determina el Empleado responsable (campo 'rut' de la OT).
    1) Si viene 'rut' en payload y existe, úsalo.
    2) Si no, intenta cualquiera del taller.
    3) Si no existe nadie, asegura/crea admin del taller.
    """
    rut = (payload.get('rut') or '').strip()
    if rut:
        emp = Empleado.objects.filter(rut=rut).first()
        if emp:
            return emp
    return _ensure_admin_for_taller(taller)

def _resolve_creador(request, payload, taller: Taller, responsable: Empleado):
    """
    Determina el Empleado 'rut_creador' (quién ingresa la OT).
    Prioridades:
      1) payload['responsable_rut'] (si lo enviaras en algún flujo)
      2) request.user (si autenticado) -> Empleado.usuario == username
      3) mismo 'responsable'
      4) admin del taller
    """
    resp_rut = (payload.get('responsable_rut') or '').strip()
    if resp_rut:
        emp = Empleado.objects.filter(rut=resp_rut).first()
        if emp:
            return emp

    user = getattr(request, 'user', None)
    if user and not isinstance(user, AnonymousUser) and user.is_authenticated:
        emp = Empleado.objects.filter(usuario=user.username).first()
        if emp:
            return emp

    return responsable or _ensure_admin_for_taller(taller)

# =======================
#        PAUSAS
# =======================
@csrf_exempt
@require_http_methods(["POST"])
def pausa_start(request, ot_id):
    ot = _get_ot_or_404(ot_id)
    if ot is None:
        return JsonResponse({"success": False, "message": "OT no encontrada"}, status=404)
    if ot.estado not in ESTADOS_EN_CURSO:
        return JsonResponse({"success": False, "message": "La OT no está en curso"}, status=400)
    if Pausa.objects.filter(ot_id=ot_id, activo=True).exists():
        return JsonResponse({"success": False, "message": "Ya existe una pausa activa"}, status=400)

    motivo = (request.POST.get("motivo") or "Pausa iniciada").strip()
    p = Pausa.objects.create(ot_id=ot_id, motivo=motivo, inicio=timezone.now(), activo=True)
    return JsonResponse({
        "success": True,
        "pausa": {"id": p.id, "inicio": p.inicio.isoformat(), "motivo": p.motivo, "activo": p.activo}
    }, status=201)

@csrf_exempt
@require_http_methods(["POST"])
def pausa_stop(request, ot_id):
    ot = _get_ot_or_404(ot_id)
    if ot is None:
        return JsonResponse({"success": False, "message": "OT no encontrada"}, status=404)
    if ot.estado not in ESTADOS_EN_CURSO:
        return JsonResponse({"success": False, "message": "La OT no está en curso"}, status=400)

    try:
        p = Pausa.objects.get(ot_id=ot_id, activo=True)
    except Pausa.DoesNotExist:
        return JsonResponse({"success": False, "message": "No hay pausa activa"}, status=400)

    p.fin = timezone.now()
    p.activo = False
    p.save(update_fields=["fin", "activo"])
    return JsonResponse({
        "success": True,
        "pausa": {"id": p.id, "fin": p.fin.isoformat(), "activo": p.activo}
    })

@require_http_methods(["GET"])
def pausa_list(request, ot_id):
    if _get_ot_or_404(ot_id) is None:
        return JsonResponse({"success": False, "message": "OT no encontrada"}, status=404)
    data = list(Pausa.objects.filter(ot_id=ot_id).order_by("-inicio").values(
        "id", "motivo", "inicio", "fin", "activo"
    ))
    return JsonResponse({"success": True, "pausas": data})

# =======================
#   AGENDA / INGRESOS
# =======================
@require_http_methods(["GET"])
def agenda_slots_api(request):
    """
    GET /api/ordenestrabajo/api/agenda/slots/?fecha=YYYY-MM-DD&taller_id=1
    Regresa slots ocupados y libres del día para un taller.

    Política:
    - Bloquea el slot por cualquier OT con hora ese día (mismo taller), excepto Cancelado.
      (Finalizadas siguen bloqueando porque el turno fue utilizado).
    """
    try:
        fecha_str = request.GET.get('fecha')
        taller_id = request.GET.get('taller_id')
        if not fecha_str or not taller_id:
            return JsonResponse({'success': False, 'message': 'Parámetros requeridos: fecha, taller_id'}, status=400)

        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Formato de fecha inválido (use YYYY-MM-DD)'}, status=400)

        try:
            taller = Taller.objects.get(pk=int(taller_id))
        except Taller.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Taller no encontrado'}, status=404)

        ots = (OrdenTrabajo.objects
               .filter(taller_id=taller.taller_id, fecha_ingreso=fecha, hora_ingreso__isnull=False)
               .exclude(estado__in=[ESTADO_CANCELADO]))

        ocupados = {ot.hora_ingreso.strftime('%H:%M') for ot in ots if ot.hora_ingreso}
        slots = _gen_slots_para_fecha(fecha)

        data = [{'hora': hstr, 'ocupado': (hstr in ocupados)} for hstr, _ in slots]
        return JsonResponse({'success': True, 'fecha': fecha_str, 'taller_id': taller.taller_id, 'slots': data})
    except Exception as e:
        logger.exception("Error en agenda_slots_api")
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def ingreso_create_api(request):
    """
    POST /api/ordenestrabajo/api/ingresos/create/
    Form-data/JSON:
      - patente (req)
      - fecha (YYYY-MM-DD, req)
      - hora (HH:MM, req)
      - taller_id (req)
      - rut (opcional: responsable de la OT)
      - responsable_rut (opcional: quién ingresa la OT; si no, se infiere)
      - descripcion (opcional)

    Reglas:
      - No solapar taller+fecha+hora si hay estados en curso.
      - No permitir mismo vehículo en estado en curso el mismo día.
    """
    try:
        payload = request.POST or json.loads(request.body.decode('utf-8') or '{}')

        patente = (payload.get('patente') or '').strip()
        fecha_str = (payload.get('fecha') or '').strip()
        hora_str = (payload.get('hora') or '').strip()
        taller_id = payload.get('taller_id')
        descripcion = (payload.get('descripcion') or '').strip() or None

        if not (patente and fecha_str and hora_str and taller_id):
            return JsonResponse({'success': False, 'message': 'Faltan parámetros requeridos (patente, fecha, hora, taller_id)'}, status=400)

        veh = Vehiculo.objects.filter(pk=patente).first()
        if not veh:
            return JsonResponse({'success': False, 'message': 'Vehículo no encontrado'}, status=404)

        try:
            taller = Taller.objects.get(pk=int(taller_id))
        except Taller.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Taller no encontrado'}, status=404)

        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            hora = datetime.strptime(hora_str, '%H:%M').time()
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Formato de fecha/hora inválido'}, status=400)

        if not (JORNADA_INICIO <= hora < JORNADA_FIN):
            return JsonResponse({'success': False, 'message': 'Hora fuera de la jornada de atención'}, status=400)

        # Conflicto: slot ya ocupado
        if OrdenTrabajo.objects.filter(
            taller_id=taller.taller_id, fecha_ingreso=fecha, hora_ingreso=hora,
            estado__in=ESTADOS_EN_CURSO
        ).exists():
            return JsonResponse({'success': False, 'message': 'El horario ya está ocupado en este taller'}, status=409)

        # Conflicto: mismo vehículo “en curso” ese día
        if OrdenTrabajo.objects.filter(
            patente=veh.patente, fecha_ingreso=fecha, estado__in=ESTADOS_EN_CURSO
        ).exists():
            return JsonResponse({'success': False, 'message': 'Este vehículo ya tiene un ingreso en curso para esa fecha'}, status=409)

        # Resolver responsable y creador (y asegurar admin si hace falta)
        responsable = _resolve_responsable(payload, taller)         # Empleado
        creador = _resolve_creador(request, payload, taller, responsable)  # Empleado

        # Crear OT – rut y rut_creador son FK a Empleado (to_field='rut')
        ot = OrdenTrabajo.objects.create(
            fecha_ingreso=fecha,
            hora_ingreso=hora,
            fecha_salida=None,
            descripcion=descripcion,
            estado='Pendiente',
            patente=veh,
            taller_id=taller.taller_id,
            rut=responsable,
            rut_creador=creador,
        )

        return JsonResponse({
            'success': True,
            'ot': {
                'id': ot.ot_id,
                'fecha': ot.fecha_ingreso.strftime('%Y-%m-%d'),
                'hora': ot.hora_ingreso.strftime('%H:%M') if ot.hora_ingreso else None,
                'estado': ot.estado,
                'patente': ot.patente.patente,
                'taller_id': ot.taller_id,
                'rut': getattr(ot.rut, 'rut', ot.rut_id),
                'rut_creador': getattr(ot.rut_creador, 'rut', None),
                'descripcion': ot.descripcion,
            }
        })
    except Exception as e:
        logger.exception("Error en ingreso_create_api")
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)

@require_http_methods(["GET"])
def ingresos_en_curso_api(request):
    """
    GET /api/ordenestrabajo/api/ingresos/en-curso/
      Filtros opcionales:
        - patente=ABC123
        - taller_id=1
        - fecha=YYYY-MM-DD
      Retorna OTs con estado en curso (Pendiente / En Proceso).
    """
    try:
        patente   = (request.GET.get('patente') or '').strip()
        fecha_str = (request.GET.get('fecha') or '').strip()
        taller_id = (request.GET.get('taller_id') or '').strip()

        qs = OrdenTrabajo.objects.filter(estado__in=ESTADOS_EN_CURSO)

        if patente:
            qs = qs.filter(patente_id=patente)

        if taller_id:
            try:
                qs = qs.filter(taller_id=int(taller_id))
            except ValueError:
                return JsonResponse({'success': False, 'message': 'taller_id inválido'}, status=400)

        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                qs = qs.filter(fecha_ingreso=fecha)
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Formato de fecha inválido'}, status=400)

        items = [{
            'id': ot.ot_id,
            'patente': ot.patente_id,
            'fecha': ot.fecha_ingreso.strftime('%Y-%m-%d') if ot.fecha_ingreso else None,
            'hora': ot.hora_ingreso.strftime('%H:%M') if ot.hora_ingreso else None,
            'estado': ot.estado,
            'taller_id': ot.taller_id,
            'rut': getattr(ot.rut, 'rut', ot.rut_id),
            'rut_creador': getattr(ot.rut_creador, 'rut', None),
            'descripcion': ot.descripcion,
        } for ot in qs.order_by('-fecha_ingreso', '-hora_ingreso', '-ot_id')]

        return JsonResponse({'success': True, 'items': items})
    except Exception as e:
        logger.exception("Error en ingresos_en_curso_api")
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST", "PATCH"])
def ingreso_finalizar_api(request, ot_id: int):
    """
    POST/PATCH /api/ordenestrabajo/api/ingresos/<ot_id>/finalizar/
    Marca la OT como Finalizado, setea fecha_salida = hoy y cierra pausas activas.
    """
    try:
        ot = _get_ot_or_404(ot_id)
        if ot is None:
            return JsonResponse({'success': False, 'message': 'OT no encontrada'}, status=404)

        if ot.estado not in ESTADOS_EN_CURSO:
            return JsonResponse({'success': False, 'message': 'La OT no está en curso'}, status=400)

        now = timezone.now()
        ot.estado = 'Finalizado'
        ot.fecha_salida = now.date()
        ot.save(update_fields=['estado', 'fecha_salida'])

        Pausa.objects.filter(ot=ot, activo=True).update(activo=False, fin=now)

        return JsonResponse({
            'success': True,
            'ot': {
                'id': ot.ot_id,
                'estado': ot.estado,
                'fecha_salida': ot.fecha_salida.strftime('%Y-%m-%d') if ot.fecha_salida else None
            }
        })
    except Exception as e:
        logger.exception("Error en ingreso_finalizar_api")
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST", "PATCH"])
def ingreso_cancelar_api(request, ot_id: int):
    """
    POST/PATCH /api/ordenestrabajo/api/ingresos/<ot_id>/cancelar/
    Marca la OT como Cancelado y cierra pausas activas (libera el slot en la agenda).
    """
    try:
        ot = _get_ot_or_404(ot_id)
        if ot is None:
            return JsonResponse({'success': False, 'message': 'OT no encontrada'}, status=404)

        if ot.estado in ('Finalizado', ESTADO_CANCELADO):
            return JsonResponse({'success': False, 'message': 'La OT no se puede cancelar en este estado'}, status=400)

        now = timezone.now()
        ot.estado = ESTADO_CANCELADO
        ot.fecha_salida = None
        ot.save(update_fields=['estado', 'fecha_salida'])

        Pausa.objects.filter(ot=ot, activo=True).update(activo=False, fin=now)

        return JsonResponse({'success': True, 'ot': {'id': ot.ot_id, 'estado': ot.estado}})
    except Exception as e:
        logger.exception("Error en ingreso_cancelar_api")
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)

# =======================
#        WHOAMI
# =======================
@require_http_methods(["GET"])
def whoami(request):
    """
    GET /api/ordenestrabajo/api/whoami/
    Devuelve rut y usuario autenticado (si existe mapeo en Empleado).
    """
    user = getattr(request, "user", None)
    rut = None
    usuario = None

    if user and not isinstance(user, AnonymousUser) and user.is_authenticated:
        usuario = user.username
        emp = Empleado.objects.filter(usuario=usuario).first()
        if emp:
            rut = emp.rut

    return JsonResponse({"rut": rut, "usuario": usuario})
