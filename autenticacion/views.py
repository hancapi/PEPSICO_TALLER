# autenticacion/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Empleado
from vehiculos.models import Vehiculo
from ordenestrabajo.models import OrdenTrabajo
import json
import logging
from django.contrib.auth import authenticate, login
logger = logging.getLogger(__name__)
from .forms import EmpleadoForm
from django.contrib.auth.hashers import make_password
from talleres.models import Taller


# ===========================
# VISTAS DE PÁGINA
# ===========================

def login_view(request):
    try:
        if request.session.get('usuario'):
            logger.info("Usuario ya autenticado, redirigiendo a /inicio/")
            return redirect('inicio')
        return render(request, 'inicio-sesion.html')
    except BrokenPipeError:
        logger.warning("Broken pipe en login_view")
        return HttpResponse(status=204)

def inicio_view(request):
    try:
        usuario = request.session.get('usuario')
        if not usuario:
            logger.warning("Usuario no autenticado, redirigiendo a /inicio-sesion/")
            return redirect('inicio-sesion')
        return render(request, 'inicio.html', {'usuario': usuario})
    except BrokenPipeError:
        logger.warning("Broken pipe en inicio_view")
        return HttpResponse(status=204)

# ===========================
# API STATUS
# ===========================

def status_api(request):
    try:
        total_empleados = Empleado.objects.count()
        return JsonResponse({
            'status': 'conectado',
            'database': f'MySQL conectado ({total_empleados} empleados)',
            'server': 'Django 4.2.25 funcionando'
        })
    except Exception as e:
        logger.error(f"Error en status_api: {str(e)}")
        return JsonResponse({
            'status': 'conectado',
            'database': f'Error BD: {str(e)}',
            'server': 'Django 4.2.25 funcionando'
        })

# ===========================
# LOGIN / LOGOUT
# ===========================

@csrf_exempt
def login_api(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        username = data.get('usuario')
        password = data.get('contrasena')

        if not username or not password:
            return JsonResponse({'success': False, 'message': 'Complete todos los campos'})

        user = authenticate(request, usuario=username, password=password)
        if user is not None:
            login(request, user)
            empleado = {
                'nombre': user.nombre,
                'rut': user.rut,
                'cargo': user.cargo,
                'region': user.region or 'No especificada',
                'horario': user.horario or 'No especificado',
                'disponibilidad': user.disponibilidad,
                'username': user.usuario
            }
            request.session['usuario'] = empleado
            return JsonResponse({'success': True, 'message': 'Login exitoso', 'empleado': empleado})
        else:
            return JsonResponse({'success': False, 'message': 'Usuario o contraseña incorrectos'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error en el servidor: {str(e)}'})


@csrf_exempt
def logout_api(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)
    try:
        request.session.flush()
        logger.info("Sesión cerrada correctamente")
        return JsonResponse({'success': True, 'message': 'Sesión cerrada correctamente'})
    except Exception as e:
        logger.error(f"Error en logout_api: {str(e)}")
        return JsonResponse({'success': False, 'message': f'No se pudo cerrar la sesión: {str(e)}'})

# ===========================
# DASHBOARD STATS
# ===========================

def dashboard_stats_api(request):
    try:
        total_vehiculos = Vehiculo.objects.count()
        en_taller = OrdenTrabajo.objects.filter(estado='Pendiente').count()
        en_proceso = OrdenTrabajo.objects.filter(estado='En Proceso').count()
        total_empleados = Empleado.objects.count()
        return JsonResponse({
            'total_vehiculos': total_vehiculos,
            'en_taller': en_taller,
            'en_proceso': en_proceso,
            'total_empleados': total_empleados
        })
    except Exception as e:
        logger.error(f"Error en dashboard_stats_api: {str(e)}")
        return JsonResponse({'error': f'No se pudieron obtener los stats: {str(e)}'}, status=500)
    
# ===========================
# REGISTRAR CHOFER
# ===========================
@csrf_exempt
def registrar_chofer(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            if Empleado.objects.filter(rut=data.get('rut')).exists():
                return JsonResponse({"success": False, "message": "El RUT ya está registrado."})

            Empleado.objects.create(
                rut=data.get('rut'),
                nombre=data.get('nombre'),
                cargo=data.get('cargo'),
                region=data.get('region'),
                horario=data.get('horario'),
                usuario=data.get('usuario'),
                password=data.get('password'),
                disponibilidad=data.get('disponibilidad'),
                taller_id=data.get('taller_id')
            )

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)
    return JsonResponse({"success": False, "message": "Método no permitido"}, status=405)

# ===========================
# VERIFICAR RUT EXISTE
# ===========================
def existe_chofer(request):
    rut = request.GET.get('rut')
    existe = Empleado.objects.filter(rut=rut).exists()
    return JsonResponse({'existe': existe})

