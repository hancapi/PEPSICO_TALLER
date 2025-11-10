# vehiculos/views.py

from datetime import datetime, timedelta
import json

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
# from django.db.models import Q  # <- importa si luego lo usas

from .models import Vehiculo
from .forms import VehiculoForm
from talleres.models import Taller
# from autenticacion.models import Empleado  # <- descomenta si lo usas
from ordenestrabajo.models import OrdenTrabajo  # KPIs/Historial
from django.contrib.auth.decorators import login_required, user_passes_test


# ==========================================================
# PÁGINAS
# ==========================================================


def puede_ingresar_vehiculos(user):
    """Permite acceso a CHOFER o SUPERVISOR."""
    return user.is_authenticated and user.groups.filter(name__in=['CHOFER', 'SUPERVISOR']).exists()

@login_required(login_url='inicio-sesion')
@user_passes_test(puede_ingresar_vehiculos, login_url='inicio')
def ingreso_vehiculos(request):
    """
    Página de Ingreso de Vehículos (form + listado rápido).
    Solo CHOFER o SUPERVISOR pueden acceder.
    """
    talleres = Taller.objects.all()

    if request.method == 'POST':
        form = VehiculoForm(request.POST)
        patente = (request.POST.get('patente') or '').strip().upper()

        if Vehiculo.objects.filter(patente=patente).exists():
            messages.error(request, "Ya existe un vehículo con esa patente.")
        elif form.is_valid():
            v = form.save(commit=False)
            v.patente = patente
            v.save()
            messages.success(request, "Vehículo registrado correctamente.")
            return redirect('vehiculos:ingreso_vehiculos')
        else:
            messages.error(request, "Error al registrar el vehículo. Revisa los datos.")
    else:
        form = VehiculoForm()

    vehiculos = Vehiculo.objects.all()
    context = {
        'form': form,
        'vehiculos': vehiculos,
        'total_vehiculos': vehiculos.count(),
        'en_taller': vehiculos.filter(estado='En Taller').count(),
        'en_proceso': vehiculos.filter(estado='En Proceso').count(),
        'disponibles': vehiculos.filter(estado='Disponible').count(),
        'talleres': talleres,
    }
    return render(request, 'ingreso-vehiculos.html', context)



def ficha_vehiculo(request, patente: str = None):
    """
    Render de la ficha. Si no viene <patente> en la ruta,
    se puede pasar por query (?patente=ABC123).
    """
    if not patente:
        patente = (request.GET.get('patente') or '').strip().upper()
    return render(request, 'ficha-vehiculo.html', {'patente': patente})


# ==========================================================
# HELPERS – fechas/filtros
# ==========================================================

def _parse_date(s: str):
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except Exception:
        return None


def _range_from_request(request):
    today = datetime.today().date()
    dfrom = _parse_date(request.GET.get('from') or '') or (today - timedelta(days=30))
    dto   = _parse_date(request.GET.get('to') or '')   or today
    if dfrom > dto:
        dfrom, dto = dto, dfrom
    return dfrom, dto


# ==========================================================
# APIS – Ingreso por JSON, existencia, ficha y historial
# ==========================================================

@csrf_exempt
def ingreso_api(request):
    """
    POST JSON para crear Vehículo.
    Body ejemplo:
    {
      "patente": "ABCZ12",
      "marca": "Ford",
      "modelo": "Ranger",
      "anio": 2020,
      "tipo_vehiculo": "Pickup",
      "ubicacion": 1   # ID de Taller (si tu modelo Vehiculo.ubicacion es texto,
                       # se guardará el nombre del taller)
    }
    """
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
    except Exception as e:
        return JsonResponse({"status": "error", "message": f"JSON inválido: {e}"}, status=400)

    patente = (data.get('patente') or '').strip().upper()
    if not patente:
        return JsonResponse({"status": "error", "message": "patente requerida"}, status=400)

    if Vehiculo.objects.filter(patente=patente).exists():
        return JsonResponse({"status": "error", "message": "La patente ya existe"}, status=400)

    # Mapear taller_id -> nombre (si tu campo ubicacion es CharField)
    taller_nombre = None
    ubicacion_in = data.get('ubicacion')
    if ubicacion_in is not None:
        try:
            t = Taller.objects.get(taller_id=ubicacion_in)
            taller_nombre = t.nombre  # guardarás el nombre en el CharField
        except Taller.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Taller no encontrado"}, status=400)

    vehiculo_data = {
        'patente': patente,
        'marca': (data.get('marca') or '').strip(),
        'modelo': (data.get('modelo') or '').strip(),
        'anio': data.get('anio') or None,
        'tipo': (data.get('tipo_vehiculo') or '').strip(),
        'estado': 'Disponible',
        # Si tu modelo tiene ubicacion = CharField, guarda el nombre del taller;
        # si en tu modelo ubicacion fuera FK, ajusta aquí a 'ubicacion_id': ubicacion_in
        'ubicacion': taller_nombre or str(ubicacion_in or '').strip(),
    }

    form = VehiculoForm(vehiculo_data)
    if form.is_valid():
        vehiculo = form.save()
        return JsonResponse({
            "status": "ok",
            "message": "Vehículo ingresado correctamente",
            "vehiculo_id": vehiculo.patente
        })
    else:
        return JsonResponse({"status": "error", "errors": form.errors}, status=400)


def existe_vehiculo(request):
    patente = (request.GET.get('patente') or '').strip().upper()
    existe = Vehiculo.objects.filter(patente=patente).exists()
    return JsonResponse({'existe': existe})


@require_GET
def api_ficha(request):
    """
    GET /vehiculos/api/ficha/?patente=ABC123
    Devuelve datos del vehículo + KPIs + OT en curso (si existe).
    """
    patente = (request.GET.get('patente') or '').strip().upper()
    if not patente:
        return JsonResponse({'success': False, 'message': 'Parámetro patente requerido'}, status=400)

    v = Vehiculo.objects.filter(pk=patente).first()
    if not v:
        return JsonResponse({
            'success': True,
            'vehiculo': None,
            'kpis': {'ots': 0, 'incidentes': 0, 'prestamos': 0, 'llave': '—'},
            'ot_actual': None
        })

    # KPIs rápidos (ajusta cuando tengas modelos Incidente/Prestamo/Llave)
    kpi_ots = OrdenTrabajo.objects.filter(patente_id=patente).count()
    kpi_inc = 0
    kpi_pres = 0
    llave = '—'

    # OT en curso (la más reciente con estado Pendiente/En Proceso)
    ot_actual = (OrdenTrabajo.objects
                 .filter(patente_id=patente, estado__in=['Pendiente', 'En Proceso'])
                 .order_by('-fecha_ingreso', '-hora_ingreso', '-ot_id')
                 .first())

    ot_payload = None
    if ot_actual:
        t_nombre = (Taller.objects
                    .filter(pk=ot_actual.taller_id)
                    .values_list('nombre', flat=True)
                    .first())
        ot_payload = {
            'id': ot_actual.ot_id,
            'fecha': ot_actual.fecha_ingreso.isoformat(),
            'hora': ot_actual.hora_ingreso.strftime('%H:%M') if ot_actual.hora_ingreso else None,
            'estado': ot_actual.estado,
            'taller_id': ot_actual.taller_id,
            'taller_nombre': t_nombre,
        }

    return JsonResponse({
        'success': True,
        'vehiculo': {
            'patente': v.patente,
            'marca': v.marca,
            'modelo': v.modelo,
            'anio': v.anio,
            'tipo': v.tipo,
            'ubicacion': v.ubicacion,
            'estado': v.estado,
        },
        'kpis': {
            'ots': kpi_ots,
            'incidentes': kpi_inc,
            'prestamos': kpi_pres,
            'llave': llave,
        },
        'ot_actual': ot_payload
    })


@require_GET
def api_ficha_ots(request):
    """
    GET /vehiculos/api/ficha/ots/?patente=ABC123&from=YYYY-MM-DD&to=YYYY-MM-DD&estado=&taller=
    Lista de OTs del vehículo con nombre de taller.
    """
    patente = (request.GET.get('patente') or '').strip().upper()
    if not patente:
        return JsonResponse({'success': False, 'message': 'Parámetro patente requerido'}, status=400)

    dfrom, dto = _range_from_request(request)
    estado = (request.GET.get('estado') or '').strip()
    taller = (request.GET.get('taller') or '').strip()

    qs = OrdenTrabajo.objects.filter(patente_id=patente, fecha_ingreso__range=(dfrom, dto))
    if estado:
        qs = qs.filter(estado=estado)

    if taller:
        # permitir ID exacto o nombre (parcial)
        if taller.isdigit():
            qs = qs.filter(taller_id=int(taller))
        else:
            ids = list(
                Taller.objects.filter(nombre__icontains=taller).values_list('taller_id', flat=True)
            )
            qs = qs.filter(taller_id__in=ids or [-1])

    # mapear nombres de taller en lote
    taller_ids = list(qs.values_list('taller_id', flat=True))
    taller_map = dict(
        Taller.objects.filter(taller_id__in=taller_ids).values_list('taller_id', 'nombre')
    )

    items = [{
        'id': ot.ot_id,
        'fecha': ot.fecha_ingreso.isoformat(),
        'hora': ot.hora_ingreso.strftime('%H:%M') if ot.hora_ingreso else None,
        'taller_id': ot.taller_id,
        'taller_nombre': taller_map.get(ot.taller_id),
        'estado': ot.estado,
        'rut': getattr(ot.rut, 'rut', None),
        'rut_creador': getattr(ot.rut_creador, 'rut', None),
    } for ot in qs.order_by('-fecha_ingreso', '-hora_ingreso', '-ot_id')]

    return JsonResponse({'success': True, 'items': items})
