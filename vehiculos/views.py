# vehiculos/views.py
from datetime import datetime, timedelta
import json

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required

from .models import Vehiculo
from .forms import VehiculoForm
from talleres.models import Taller
from ordenestrabajo.models import OrdenTrabajo
from autenticacion.models import Empleado

from autenticacion.roles import (
    chofer_or_supervisor,
    mecanico_or_supervisor,
    todos_roles,
)

# ==========================================================
# PÁGINAS HTML
# ==========================================================

@login_required(login_url="/inicio-sesion/")
@chofer_or_supervisor
def ingreso_vehiculos(request):
    """Página de ingreso de vehículos (solo CHOFER o SUPERVISOR)"""
    user = request.user

    try:
        empleado = Empleado.objects.select_related('taller').get(usuario=user.username)
    except Empleado.DoesNotExist:
        empleado = None

    talleres = Taller.objects.all()

    if request.method == 'POST':
        form = VehiculoForm(request.POST)
        patente = (request.POST.get('patente') or '').strip().upper()

        if Vehiculo.objects.filter(patente=patente).exists():
            messages.error(request, "⚠️ Ya existe un vehículo con esa patente.")

        elif form.is_valid():
            v = form.save(commit=False)
            v.patente = patente
            v.save()
            messages.success(request, "✅ Vehículo registrado correctamente.")
            return redirect('vehiculos:ingreso_vehiculos')

        else:
            messages.error(request, "❌ Error al registrar el vehículo.")

    else:
        form = VehiculoForm()

    vehiculos = Vehiculo.objects.all().order_by('-patente')

    return render(request, 'ingreso-vehiculos.html', {
        'form': form,
        'vehiculos': vehiculos,
        'talleres': talleres,
        'empleado': empleado,
        'menu_active': 'ingreso_vehiculos',
    })


@login_required(login_url="/inicio-sesion/")
@todos_roles
def ficha_vehiculo(request, patente: str = None):
    """Todos pueden ver la ficha del vehículo"""
    if not patente:
        patente = request.GET.get('patente', '').strip().upper()

    user = request.user
    try:
        empleado = Empleado.objects.select_related('taller').get(usuario=user.username)
    except Empleado.DoesNotExist:
        empleado = None

    return render(request, 'ficha-vehiculo.html', {
        'patente': patente,
        'empleado': empleado,
        'menu_active': 'ficha_vehiculo'
    })


# ==========================================================
# HELPERS
# ==========================================================

def _parse_date(s: str):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except:
        return None


def _range_from_request(request):
    today = datetime.today().date()
    dfrom = _parse_date(request.GET.get("from") or "") or (today - timedelta(days=30))
    dto = _parse_date(request.GET.get("to") or "") or today
    if dfrom > dto:
        dfrom, dto = dto, dfrom
    return dfrom, dto


# ==========================================================
# APIS
# ==========================================================

@require_POST
@login_required
@chofer_or_supervisor
def ingreso_api(request):
    """
    API JSON – Registrar vehículo
    """
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except:
        return JsonResponse({"status": "error", "message": "JSON inválido"}, status=400)

    patente = (data.get("patente") or "").strip().upper()
    if not patente:
        return JsonResponse({"status": "error", "message": "Patente requerida"}, status=400)

    if Vehiculo.objects.filter(patente=patente).exists():
        return JsonResponse({"status": "error", "message": "La patente ya existe"}, status=400)

    # Ubicación → charfield
    ubicacion = (data.get("ubicacion") or "").strip()

    vehiculo_data = {
        "patente": patente,
        "marca": (data.get("marca") or "").strip(),
        "modelo": (data.get("modelo") or "").strip(),
        "anio": data.get("anio") or None,
        "tipo": (data.get("tipo_vehiculo") or "").strip(),
        "estado": "Disponible",
        "ubicacion": ubicacion,
    }

    form = VehiculoForm(vehiculo_data)
    if form.is_valid():
        vehiculo = form.save()
        return JsonResponse({
            "status": "ok",
            "message": "Vehículo ingresado correctamente",
            "vehiculo_id": vehiculo.patente
        })

    return JsonResponse({"status": "error", "errors": form.errors}, status=400)


@require_GET
def existe_vehiculo(request):
    patente = (request.GET.get("patente") or "").strip().upper()
    existe = Vehiculo.objects.filter(patente=patente).exists()
    return JsonResponse({"existe": existe})


# ==========================================================
# API Ficha datos generales + OT actual
# ==========================================================

@require_GET
@login_required
@todos_roles
def api_ficha(request):
    """Ficha de vehículo"""
    patente = (request.GET.get('patente') or "").strip().upper()
    if not patente:
        return JsonResponse({'success': False, 'message': 'Parámetro patente requerido'}, status=400)

    v = Vehiculo.objects.filter(pk=patente).first()
    if not v:
        return JsonResponse({
            'success': True,
            'vehiculo': None,
            'kpis': {'ots': 0},
            'ot_actual': None
        })

    kpi_ots = OrdenTrabajo.objects.filter(patente_id=patente).count()

    ot_actual = (
        OrdenTrabajo.objects
            .filter(patente_id=patente, estado__in=["Pendiente", "En Proceso"])
            .order_by('-fecha_ingreso', '-hora_ingreso')
            .first()
    )

    ot_payload = None
    if ot_actual:
        taller_nombre = (
            Taller.objects
            .filter(pk=ot_actual.taller_id)
            .values_list('nombre', flat=True)
            .first()
        )
        ot_payload = {
            'id': ot_actual.ot_id,
            'fecha': ot_actual.fecha_ingreso.isoformat(),
            'hora': ot_actual.hora_ingreso.strftime('%H:%M') if ot_actual.hora_ingreso else None,
            'estado': ot_actual.estado,
            'taller_id': ot_actual.taller_id,
            'taller_nombre': taller_nombre,
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
        'kpis': {'ots': kpi_ots},
        'ot_actual': ot_payload
    })


# ==========================================================
# API Historial
# ==========================================================

@require_GET
@login_required
@todos_roles
def api_ficha_ots(request):
    """Historial de OTs por vehículo"""
    patente = (request.GET.get('patente') or "").strip().upper()
    if not patente:
        return JsonResponse({'success': False, 'message': 'Parámetro patente requerido'}, status=400)

    dfrom, dto = _range_from_request(request)
    estado = (request.GET.get('estado') or "").strip()
    taller = (request.GET.get('taller') or "").strip()

    qs = OrdenTrabajo.objects.filter(
        patente_id=patente,
        fecha_ingreso__range=(dfrom, dto)
    )

    if estado:
        qs = qs.filter(estado=estado)

    if taller:
        if taller.isdigit():
            qs = qs.filter(taller_id=int(taller))
        else:
            ids = list(Taller.objects.filter(nombre__icontains=taller)
                                      .values_list('taller_id', flat=True))
            qs = qs.filter(taller_id__in=ids or [-1])

    # Map de talleres
    taller_ids = list(qs.values_list('taller_id', flat=True))
    taller_map = dict(Taller.objects.filter(taller_id__in=taller_ids)
                                    .values_list('taller_id', 'nombre'))

    items = []
    for ot in qs.order_by('-fecha_ingreso', '-hora_ingreso', '-ot_id'):
        items.append({
            'id': ot.ot_id,
            'fecha': ot.fecha_ingreso.isoformat(),
            'hora': ot.hora_ingreso.strftime('%H:%M') if ot.hora_ingreso else None,
            'taller_id': ot.taller_id,
            'taller_nombre': taller_map.get(ot.taller_id),
            'estado': ot.estado,
            'rut': getattr(ot.rut, 'rut', None),
            'rut_creador': getattr(ot.rut_creador, 'rut', None),
        })

    return JsonResponse({'success': True, 'items': items})
