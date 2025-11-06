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


@csrf_exempt
def obtener_horarios(request):
    fecha_str = request.GET.get('fecha')
    if not fecha_str:
        return JsonResponse({"error": "Fecha no proporcionada"}, status=400)

    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({"error": "Formato de fecha inválido"}, status=400)

    # 🔹 Cambiar campos a los correctos
    ocupadas = list(
        OrdenTrabajo.objects
        .filter(fecha_ingreso=fecha)
        .values_list('hora_ingreso', flat=True)
    )

    # Convertir objetos time a string
    ocupadas = [h.strftime('%H:%M') for h in ocupadas if h]

    return JsonResponse({"ocupadas": ocupadas})


def horarios_ocupados(request):
    ordenes = OrdenTrabajo.objects.all()
    ocupados = {}

    for orden in ordenes:
        fecha = orden.fecha_ingreso.strftime('%Y-%m-%d')
        if orden.hora_ingreso:
            hora = orden.hora_ingreso.strftime('%H:%M')
            ocupados.setdefault(fecha, []).append(hora)

    return JsonResponse(ocupados)



@csrf_exempt
def registrar_orden_trabajo(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Verificar o registrar vehículo
            patente = data.get('patente')
            vehiculo = Vehiculo.objects.filter(patente=patente).first()
            if not vehiculo:
                taller = Taller.objects.get(taller_id=data.get('ubicacion'))
                vehiculo = Vehiculo.objects.create(
                    patente=patente,
                    marca=data.get('marca'),
                    modelo=data.get('modelo'),
                    anio=data.get('anio'),
                    tipo=data.get('tipo_vehiculo'),
                    estado='Disponible',
                    ubicacion=taller
                )

            # Verificar chofer
            rut = data.get('rut')
            if not Empleado.objects.filter(rut=rut).exists():
                return JsonResponse({
                    "status": "nuevo_chofer",
                    "message": "Este RUT no está registrado. Completa los datos del nuevo chofer."
                })

            # Registrar orden
            OrdenTrabajo.objects.create(
                vehiculo=vehiculo,
                rut_chofer=rut,
                fecha=data.get('fecha'),
                hora=data.get('hora'),
                tipo_mantenimiento=data.get('tipo_mantenimiento'),
                kilometraje=data.get('kilometraje'),
                descripcion=data.get('descripcion'),
                estado='Pendiente'
            )

            return JsonResponse({
                "status": "ok",
                "message": "Ingreso registrado correctamente."
            })

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)
