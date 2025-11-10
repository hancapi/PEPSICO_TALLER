from datetime import datetime, timedelta
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from ordenestrabajo.models import OrdenTrabajo
from vehiculos.models import Vehiculo
from autenticacion.models import Empleado
from common.decorators import role_required

# Página
@role_required(["SUPERVISOR"])
def reportes_page(request):
    return render(request, 'reportes.html')

# Helpers fechas
def _parse_date(s: str):
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except Exception:
        return None

def _get_range(request):
    """Devuelve (from_date, to_date) con defaults últimos 7 días si vienen vacíos/mal formateados."""
    today = datetime.today().date()
    default_from = today - timedelta(days=7)
    s_from = (request.GET.get('from') or '').strip()
    s_to   = (request.GET.get('to')   or '').strip()

    d_from = _parse_date(s_from) if s_from else default_from
    d_to   = _parse_date(s_to)   if s_to   else today

    if d_from > d_to:
        d_from, d_to = d_to, d_from
    return d_from, d_to

@require_GET
def api_summary(request):
    d_from, d_to = _get_range(request)

    vehiculos_totales = Vehiculo.objects.count()
    en_curso = OrdenTrabajo.objects.filter(estado__in=['Pendiente', 'En Proceso']).count()
    en_taller = (OrdenTrabajo.objects
                 .filter(fecha_ingreso__range=(d_from, d_to))
                 .exclude(estado='Cancelado')
                 .count())
    empleados_activos = Empleado.objects.filter(is_active=True).count()

    return JsonResponse({
        'success': True,
        'range': {'from': d_from.isoformat(), 'to': d_to.isoformat()},
        'kpis': {
            'vehiculos_totales': vehiculos_totales,
            'en_taller': en_taller,
            'en_proceso': en_curso,
            'empleados_activos': empleados_activos,
        }
    })

@require_GET
def api_ots(request):
    d_from, d_to = _get_range(request)

    # Filtros opcionales
    patente     = (request.GET.get('patente') or '').strip().upper()
    estado      = (request.GET.get('estado') or '').strip()
    taller_id   = (request.GET.get('taller_id') or '').strip()
    rut_creador = (request.GET.get('rut_creador') or '').strip()

    qs = (OrdenTrabajo.objects
          .select_related('taller', 'rut_creador')  # para usar nombre del taller y rut creador
          .filter(fecha_ingreso__range=(d_from, d_to))
          .order_by('-fecha_ingreso', '-hora_ingreso', '-ot_id'))

    if patente:
        qs = qs.filter(patente_id=patente)
    if estado:
        qs = qs.filter(estado=estado)
    if taller_id:
        qs = qs.filter(taller_id=taller_id)
    if rut_creador:
        qs = qs.filter(rut_creador__rut=rut_creador)

    items = [{
        'id': ot.ot_id,
        'fecha': ot.fecha_ingreso.isoformat(),
        'hora': ot.hora_ingreso.strftime('%H:%M') if ot.hora_ingreso else None,
        'patente': ot.patente_id,
        'taller_id': ot.taller_id,
        'taller_nombre': getattr(ot.taller, 'nombre', str(ot.taller_id)),
        'estado': ot.estado,
        'rut_creador': getattr(ot.rut_creador, 'rut', None),
    } for ot in qs]

    return JsonResponse({
        'success': True,
        'range': {'from': d_from.isoformat(), 'to': d_to.isoformat()},
        'items': items
    })
