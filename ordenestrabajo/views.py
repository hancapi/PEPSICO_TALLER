#ordenestrabajo/views.py
from vehiculos.models import Vehiculo
from autenticacion.models import Empleado
from talleres.models import Taller
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from ordenestrabajo.models import OrdenTrabajo
from rest_framework import viewsets
from .models import OrdenTrabajo
from .serializers import OrdenTrabajoSerializer
from datetime import datetime


class OrdenTrabajoViewSet(viewsets.ModelViewSet):
    queryset = OrdenTrabajo.objects.all()
    serializer_class = OrdenTrabajoSerializer

def horarios_ocupados(request):
    ordenes = OrdenTrabajo.objects.all()
    ocupados = {}

    for orden in ordenes:
        fecha = orden.fecha_ingreso.strftime('%Y-%m-%d')
        hora = orden.hora_ingreso.strftime('%H:%M')
        ocupados.setdefault(fecha, []).append(hora)

    return JsonResponse(ocupados)


@csrf_exempt
def registrar_ingreso(request):
    if request.method == 'OPTIONS':
        return JsonResponse({'status': 'ok', 'message': 'Preflight permitido'})

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("Datos recibidos:", data)

            # Conversión segura de fecha y hora
            try:
                fecha = datetime.strptime(data.get('fecha'), "%Y-%m-%d").date()
                hora = datetime.strptime(data.get('hora'), "%H:%M").time()
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Formato de fecha u hora inválido'}, status=400)

            patente = (data.get('patente') or '').strip().upper()
            rut = (data.get('rut') or '').strip()
            descripcion = (data.get('descripcion') or '').strip() or "Sin descripción"


            if not fecha or not hora or not patente or not rut:
                return JsonResponse({'status': 'error', 'message': 'Faltan campos obligatorios'}, status=400)

            if OrdenTrabajo.objects.filter(fecha_ingreso=fecha, hora_ingreso=hora).exists():
                return JsonResponse({'status': 'error', 'message': 'Ya existe una orden en ese horario'}, status=400)

            # Vehículo
            try:
                vehiculo = Vehiculo.objects.get(patente=patente)
            except Vehiculo.DoesNotExist:
                marca = data.get('marca')
                modelo = data.get('modelo')
                tipo_vehiculo = data.get('tipo_vehiculo')
                ubicacion = data.get('ubicacion')
                anio = data.get('anio')

                if not marca or not modelo or not tipo_vehiculo or not ubicacion or not anio:
                    return JsonResponse({'status': 'error', 'message': 'Debes completar los datos del vehículo nuevo'}, status=400)

                try:
                    anio = int(anio)
                    if anio < 1900 or anio > datetime.now().year + 1:
                        raise ValueError
                except ValueError:
                    return JsonResponse({'status': 'error', 'message': 'Año del vehículo inválido'}, status=400)

                vehiculo = Vehiculo.objects.create(
                    patente=patente,
                    marca=marca,
                    modelo=modelo,
                    tipo=tipo_vehiculo,
                    ubicacion=ubicacion,
                    anio=anio,
                    estado='Disponible'
                )
                print("Vehículo nuevo creado:", patente)

            # Chofer
            try:
                empleado = Empleado.objects.get(rut=rut)
            except Empleado.DoesNotExist:
                nombre = data.get('nombre_chofer')
                cargo = data.get('cargo_chofer')
                region = data.get('region_chofer')
                horario = data.get('horario_chofer')
                disponibilidad = data.get('disponibilidad_chofer')
                usuario = data.get('usuario_chofer')

                if not nombre or not cargo or not region or not horario or not usuario:
                    return JsonResponse({
                        'status': 'nuevo_chofer',
                        'message': 'El RUT no está registrado. Completa los datos del nuevo chofer en el formulario.',
                    }, status=200)

                empleado = Empleado.objects.create(
                    rut=rut,
                    nombre=nombre.strip().title(),
                    cargo=cargo.strip().capitalize(),
                    region=region.strip().title() if region else None,
                    horario=horario.strip() if horario else None,
                    disponibilidad='Disponible' if disponibilidad else 'No disponible',
                    usuario=usuario.strip()
                )

                print("Chofer nuevo creado:", rut)

            # Taller
            try:
                taller = Taller.objects.get(taller_id=1)
            except Taller.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'El taller no existe'}, status=400)

            # Crear orden de trabajo
            OrdenTrabajo.objects.create(
                fecha_ingreso=fecha,
                hora_ingreso=hora,
                descripcion=descripcion,
                estado='Pendiente',
                patente=vehiculo,
                taller=taller,
                empleado=empleado
            )

            return JsonResponse({'status': 'ok', 'message': 'Ingreso registrado correctamente'})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)
