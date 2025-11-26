# autenticacion/views.py
import json
import logging

from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.db import connection, OperationalError
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout

from autenticacion.models import Empleado
from vehiculos.models import Vehiculo
from ordenestrabajo.models import OrdenTrabajo

logger = logging.getLogger(__name__)


# ==========================================================
# HELPERS
# ==========================================================
def _ok_db() -> bool:
    """Verifica si la conexión a la base de datos está activa."""
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return True
    except OperationalError:
        return False


def _empleado_payload(emp: Empleado) -> dict:
    """Serializa un Empleado para envío al frontend."""
    # Usamos recinto, pero mantenemos la clave 'taller' por compatibilidad
    recinto = getattr(emp, "recinto", None)

    return {
        "rut": emp.rut,
        "usuario": emp.usuario,
        "nombre": emp.nombre,
        "cargo": emp.cargo,
        "region": emp.region or "No especificada",
        "horario": emp.horario or "No especificado",
        "disponibilidad": int(emp.disponibilidad),

        # Antes esto era realmente el TALLER; ahora exponemos el RECINTO
        # pero conservando la estructura para no romper los clientes.
        "taller": {
            "taller_id": recinto.recinto_id if recinto else None,
            "nombre": recinto.nombre if recinto else "Sin recinto",
            "ubicacion": recinto.ubicacion if recinto else "-",
        },

        "is_staff": bool(emp.is_staff),
        "is_active": bool(emp.is_active),
        "is_superuser": bool(emp.is_superuser),
    }


# ==========================================================
# STATUS
# ==========================================================
@require_GET
def status_view(request):
    """Verifica conectividad y estado del servidor."""
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
            "status": "error",
            "database": f"Error BD: {str(e)}",
            "server": "Django 4.2.25 funcionando"
        })


# ==========================================================
# LOGIN
# ==========================================================
@csrf_exempt
@require_POST
def login_view(request):
    """Login API JSON."""
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'JSON inválido'}, status=400)

    username = (data.get('usuario') or '').strip()
    password = (data.get('contrasena') or '').strip()

    if not username or not password:
        return JsonResponse({'success': False, 'message': 'Complete todos los campos'}, status=400)

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse({'success': False, 'message': 'Usuario o contraseña incorrectos'}, status=401)

    login(request, user)

    try:
        # ANTES: select_related('taller')
        emp = Empleado.objects.select_related('recinto').get(usuario=username)
    except Empleado.DoesNotExist:
        logger.warning(f"Empleado no encontrado para usuario {username}")
        return JsonResponse({'success': False, 'message': 'Empleado no encontrado'}, status=404)

    return JsonResponse({
        'success': True,
        'message': 'Login exitoso',
        'empleado': _empleado_payload(emp)
    })


# ==========================================================
# LOGOUT (API JSON)
# ==========================================================
@csrf_exempt
def logout_view(request):
    """Logout API JSON (usado por aplicaciones externas o SPA)."""
    try:
        logout(request)
        return JsonResponse({'success': True, 'message': 'Sesión cerrada correctamente'})
    except Exception as e:
        logger.error(f"Error en logout_view: {e}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# ==========================================================
# LOGOUT PARA HTML
# ==========================================================
def logout_web_view(request):
    """Logout tradicional, usado por el botón 'Cerrar Sesión' en HTML."""
    try:
        logout(request)
        return redirect('inicio-sesion')
    except Exception as e:
        logger.error(f"Error en logout_web_view: {e}")
        return redirect('inicio-sesion')


# ==========================================================
# DASHBOARD STATS
# ==========================================================
@require_GET
def dashboard_stats_view(request):
    """Indicadores del dashboard (Inicio)."""
    try:
        total_vehiculos = Vehiculo.objects.count()
        total_empleados = Empleado.objects.filter(is_active=True).count()

        qs_abiertas = OrdenTrabajo.objects.filter(fecha_salida__isnull=True)

        return JsonResponse({
            'success': True,
            'kpis': {
                'total_vehiculos': total_vehiculos,
                'en_taller': qs_abiertas.count(),
                'en_proceso': qs_abiertas.filter(
                    Q(estado__iexact='En proceso') | Q(estado__iexact='Pendiente')
                ).count(),
                'total_empleados': total_empleados,
            }
        })

    except Exception as e:
        logger.error(f"Error dashboard_stats_view: {e}")
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

# autenticacion/views.py 
from django.contrib.auth.decorators import login_required
from autenticacion.roles import admin_web_only


@login_required(login_url='/inicio-sesion/')
@admin_web_only
def panel_admin_web(request):
    """
    Panel de administración funcional para el cliente.
    Solo accesible para empleados con cargo ADMIN_WEB.
    """
    return render(request, "admin_panel.html", {
        "menu_active": "admin_web"
    })
