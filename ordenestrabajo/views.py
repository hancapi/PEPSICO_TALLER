from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework import viewsets
from datetime import datetime
import json

from vehiculos.models import Vehiculo
from autenticacion.models import Empleado
from talleres.models import Taller
from .models import OrdenTrabajo
from .serializers import OrdenTrabajoSerializer


class OrdenTrabajoViewSet(viewsets.ModelViewSet):
    queryset = OrdenTrabajo.objects.all()
    serializer_class = OrdenTrabajoSerializer


def horarios_ocupados(request):
    """
    Retorna todas las fechas y horas ocupadas en formato JSON
    para marcar en el calendario del frontend.
    """
    ordenes = OrdenTrabajo.objects.all()
    ocupados = {}

    for orden in ordenes:
        if not orden.fecha_ingreso or not orden.hora_ingreso:
            continue

        fecha = orden.fecha_ingreso.strftime('%Y-%m-%d')
        hora = orden.hora_ingreso.strftime('%H:%M')

        if fecha not in ocupados:
            ocupados[fecha] = []
        ocupados[fecha].append(hora)

    return JsonResponse(ocupados)


@csrf_exempt
def registrar_orden_trabajo(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            patente = data.get('patente')
            rut = data.get('rut')

            # Obtener taller
            taller = Taller.objects.get(taller_id=data.get('ubicacion'))

            # Verificar vehículo existente
            vehiculo = Vehiculo.objects.filter(patente=patente).first()
            if not vehiculo:
                return JsonResponse({
                    "status": "vehiculo_no_existe",
                    "message": "El vehículo con esta patente no existe en el sistema."
                }, status=200)

            # Verificar chofer
            chofer = Empleado.objects.filter(rut=rut).first()
            if not chofer:
                return JsonResponse({
                    "status": "nuevo_chofer",
                    "message": "Este RUT no está registrado. Completa los datos del nuevo chofer."
                }, status=200)

            # Crear la orden
            OrdenTrabajo.objects.create(
                fecha_ingreso=data.get('fecha'),
                hora_ingreso=data.get('hora'),
                descripcion=data.get('descripcion'),
                estado='Pendiente',
                patente=vehiculo,
                taller=taller,
                rut=chofer
            )

            return JsonResponse({
                "status": "ok",
                "message": "Orden de trabajo registrada correctamente."
            })

        except Taller.DoesNotExist:
            return JsonResponse({
                "status": "error",
                "message": "El taller seleccionado no existe."
            }, status=400)

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=400)

    return JsonResponse({
        "status": "error",
        "message": "Método no permitido"
    }, status=405)
