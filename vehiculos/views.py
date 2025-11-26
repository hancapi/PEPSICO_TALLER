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
from talleres.models import Taller  # sigue existiendo para otros usos
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
        # antes: select_related('taller')
        empleado = Empleado.objects.select_related('recinto').get(usuario=user.username)
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
        # antes: select_related('taller')
        empleado = Empleado.objects.select_related('recinto').get(usuario=user.username)
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
# API Ficha datos generales + OT actual + Documentos agrupados
# ==========================================================

@require_GET
@login_required
@todos_roles
def api_ficha(request):
    """Ficha completa del vehículo"""
    patente = (request.GET.get('patente') or "").strip().upper()
    if not patente:
        return JsonResponse({'success': False, 'message': 'Parámetro patente requerido'}, status=400)

    # VEHÍCULO
    v = Vehiculo.objects.filter(pk=patente).first()
    if not v:
        return JsonResponse({
            'success': True,
            'vehiculo': None,
            'kpis': {'ots': 0},
            'ot_actual': None,
            'documentos': {
                "actual": [],
                "finalizadas": [],
                "vehiculo": []
            }
        })

    # KPI
    kpi_ots = OrdenTrabajo.objects.filter(patente_id=patente).count()

    # OT ACTUAL
    estados_activos = ["Pendiente", "Recibida", "En Taller", "En Proceso", "Pausado"]

    ot_actual = (
        OrdenTrabajo.objects
            .filter(patente_id=patente, estado__in=estados_activos)
            .select_related("recinto")
            .order_by('-fecha_ingreso', '-hora_ingreso')
            .first()
    )

    ot_payload = None
    if ot_actual:
        # OrdenTrabajo ahora tiene recinto, no taller.
        taller_id = getattr(ot_actual, "recinto_id", None)
        taller_nombre = getattr(ot_actual.recinto, "nombre", None) if ot_actual.recinto_id else None

        ot_payload = {
            'id': ot_actual.ot_id,
            'fecha': ot_actual.fecha_ingreso.isoformat(),
            'hora': ot_actual.hora_ingreso.strftime('%H:%M') if ot_actual.hora_ingreso else None,
            'estado': ot_actual.estado,
            # mantenemos las mismas claves que espera el JS, pero usando recinto
            'taller_id': taller_id,
            'taller_nombre': taller_nombre,
        }

    # DOCUMENTOS AGRUPADOS
    from documentos.models import Documento

    # Documentos OT actual
    docs_ot_actual = []
    if ot_actual:
        docs_ot_actual = [
            {
                "id": d.id,
                "titulo": d.titulo,
                "tipo": d.tipo,
                "archivo": d.archivo.url if d.archivo else "",
                "creado_en": d.creado_en.strftime("%Y-%m-%d %H:%M")
            }
            for d in Documento.objects.filter(ot_id=ot_actual.ot_id).order_by("-creado_en")
        ]

    # Documentos de OTs finalizadas
    ots_finalizadas_ids = list(
        OrdenTrabajo.objects.filter(
            patente_id=patente,
            estado="Finalizado"
        ).values_list("ot_id", flat=True)
    )

    docs_ots_finalizadas = [
        {
            "id": d.id,
            "titulo": d.titulo,
            "tipo": d.tipo,
            "archivo": d.archivo.url if d.archivo else "",
            "creado_en": d.creado_en.strftime("%Y-%m-%d %H:%M"),
            "ot_id": d.ot_id
        }
        for d in Documento.objects.filter(ot_id__in=ots_finalizadas_ids).order_by("-creado_en")
    ]

    # Documentos sueltos (vehículo)
    docs_vehiculo = [
        {
            "id": d.id,
            "titulo": d.titulo,
            "tipo": d.tipo,
            "archivo": d.archivo.url if d.archivo else "",
            "creado_en": d.creado_en.strftime("%Y-%m-%d %H:%M")
        }
        for d in Documento.objects.filter(patente_id=patente, ot__isnull=True).order_by("-creado_en")
    ]

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
        'ot_actual': ot_payload,
        'documentos': {
            "actual": docs_ot_actual,
            "finalizadas": docs_ots_finalizadas,
            "vehiculo": docs_vehiculo
        }
    })


@require_GET
@login_required
@todos_roles
def api_ficha_ots(request):
    """Historial de OTs por vehículo (para ficha_vehiculo)"""
    patente = (request.GET.get('patente') or "").strip().upper()
    if not patente:
        return JsonResponse(
            {'success': False, 'message': 'Parámetro patente requerido'},
            status=400
        )

    # Base: TODAS las OTs del vehículo
    qs = OrdenTrabajo.objects.filter(patente_id=patente).select_related("recinto")

    # Rango de fechas opcional
    if request.GET.get("from") or request.GET.get("to"):
        dfrom, dto = _range_from_request(request)
        qs = qs.filter(fecha_ingreso__range=(dfrom, dto))

    estado = (request.GET.get('estado') or "").strip()
    filtro_taller = (request.GET.get('taller') or "").strip()

    if estado:
        qs = qs.filter(estado=estado)

    # Ahora filtramos por nombre de recinto (taller lógico)
    if filtro_taller:
        qs = qs.filter(recinto__nombre__icontains=filtro_taller)

    items = []
    for ot in qs.order_by('-fecha_ingreso', '-hora_ingreso', '-ot_id'):
        items.append({
            'id': ot.ot_id,
            'fecha': ot.fecha_ingreso.isoformat(),
            'hora': ot.hora_ingreso.strftime('%H:%M') if ot.hora_ingreso else None,
            # mismas claves que esperaba el JS, pero usando recinto
            'taller_id': getattr(ot, "recinto_id", None),
            'taller_nombre': getattr(ot.recinto, "nombre", None) if ot.recinto_id else None,
            'estado': ot.estado,
            'rut': getattr(ot.rut, 'rut', None),
            'rut_creador': getattr(ot.rut_creador, 'rut', None),
            'descripcion': ot.descripcion or "",
        })

    return JsonResponse({'success': True, 'items': items})
