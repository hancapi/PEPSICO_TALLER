# autenticacion/views.py
import json
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.db import connection, OperationalError
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout

from autenticacion.models import Empleado
from vehiculos.models import Vehiculo
from ordenestrabajo.models import OrdenTrabajo

logger = logging.getLogger(__name__)

# ===========================
# HELPERS
# ===========================

def _ok_db():
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return True
    except OperationalError:
        return False

def _empleado_payload(emp: Empleado):
    """
    Serializa el empleado para el front.
    """
    return {
        "rut": emp.rut,
        "usuario": emp.usuario,
        "nombre": emp.nombre,
        "cargo": emp.cargo,
        "region": emp.region or "No especificada",
        "horario": emp.horario or "No especificado",
        "disponibilidad": int(emp.disponibilidad),  # 0/1
        "taller": {
            "taller_id": emp.taller_id,
            "nombre": emp.taller.nombre,
            "ubicacion": emp.taller.ubicacion,
        },
        "is_staff": bool(emp.is_staff),
        "is_active": bool(emp.is_active),
        "is_superuser": bool(emp.is_superuser),
    }

# ===========================
# API: STATUS
# ===========================

@require_GET
def status_view(request):
    """
    GET /api/autenticacion/status/
    Respuesta compatible con tu login.js (usa claves: status, database, server).
    """
    try:
        total_empleados = Empleado.objects.count()
        db_ok = _ok_db()
        return JsonResponse({
            "status": "conectado",
            "database": f"MySQL conectado ({total_empleados} empleados)" if db_ok else "Error BD",
            "server": "Django 4.2.25 funcionando"
        })
    except Exception as e:
        logger.error(f"Error en status_view: {e}")
        return JsonResponse({
            "status": "conectado",
            "database": f"Error BD: {str(e)}",
            "server": "Django 4.2.25 funcionando"
        })

# ===========================
# API: LOGIN / LOGOUT
# ===========================

@csrf_exempt
def login_view(request):
    """
    POST JSON: { "usuario": "...", "contrasena": "..." }
    - Autentica con tu EmpleadosBackend (authenticate(username=..., password=...))
    - Crea sesión Django
    - Devuelve payload para localStorage: { success, message, empleado }
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'JSON inválido'}, status=400)

    username = (data.get('usuario') or '').strip()
    password = (data.get('contrasena') or '').strip()

    if not username or not password:
        return JsonResponse({'success': False, 'message': 'Complete todos los campos'}, status=400)

    # IMPORTANTE: usar 'username' y 'password'
    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({'success': False, 'message': 'Usuario o contraseña incorrectos'}, status=401)

    # Crea sesión Django
    login(request, user)

    # Cargar datos del empleado real (tabla empleados)
    try:
        emp = Empleado.objects.select_related('taller').get(usuario=username)
    except Empleado.DoesNotExist:
        # Muy raro si authenticate pasó, pero lo manejamos
        return JsonResponse({'success': False, 'message': 'Empleado no encontrado'}, status=404)

    empleado_payload = _empleado_payload(emp)
    return JsonResponse({'success': True, 'message': 'Login exitoso', 'empleado': empleado_payload})


@csrf_exempt
def logout_view(request):
    """
    POST/GET /api/autenticacion/logout/
    - Cierra sesión Django
    """
    if request.method not in ('POST', 'GET'):
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)
    try:
        logout(request)
        return JsonResponse({'success': True, 'message': 'Sesión cerrada correctamente'})
    except Exception as e:
        logger.error(f"Error en logout_view: {e}")
        return JsonResponse({'success': False, 'message': f'No se pudo cerrar la sesión: {str(e)}'})

# ===========================
# API: DASHBOARD STATS
# ===========================

@require_GET
def dashboard_stats_view(request):
    """
    GET /api/autenticacion/dashboard-stats/
    Resumen para tarjetas del dashboard.

    Definiciones (MVP):
      - total_vehiculos: total de registros en 'vehiculos'
      - total_empleados: empleados activos (is_active = 1)
      - en_taller: OTs con fecha_salida IS NULL (vehículo aún en taller)
      - en_proceso: OTs abiertas con estado 'Pendiente' o 'En proceso' (insensible a mayúsculas)
    """
    try:
        total_vehiculos = Vehiculo.objects.count()
        total_empleados = Empleado.objects.filter(is_active=True).count()

        qs_abiertas = OrdenTrabajo.objects.filter(fecha_salida__isnull=True)
        en_taller = qs_abiertas.count()
        en_proceso = qs_abiertas.filter(
            Q(estado__iexact='En proceso') | Q(estado__iexact='Pendiente')
        ).count()

        return JsonResponse({
            'total_vehiculos': total_vehiculos,
            'en_taller': en_taller,
            'en_proceso': en_proceso,
            'total_empleados': total_empleados
        })
    except Exception as e:
        logger.error(f"Error en dashboard_stats_view: {e}")
        return JsonResponse({'error': f'No se pudieron obtener los stats: {str(e)}'}, status=500)
