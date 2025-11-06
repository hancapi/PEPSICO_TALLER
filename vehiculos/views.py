# vehiculos/views.py
from django.shortcuts import render, redirect
from .models import Vehiculo
from .forms import VehiculoForm
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from talleres.models import Taller
import json

def ingreso_vehiculos_view(request):
    talleres = Taller.objects.all()

    if request.method == 'POST':
        form = VehiculoForm(request.POST)
        patente = request.POST.get('patente')

        if Vehiculo.objects.filter(patente=patente).exists():
            messages.error(request, "Ya existe un vehículo con esa patente.")
        elif form.is_valid():
            form.save()
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


@csrf_exempt
def ingreso_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Convertir taller_id a objeto Taller
            taller_id = data.get('ubicacion')
            try:
                taller_obj = Taller.objects.get(taller_id=taller_id)
            except Taller.DoesNotExist:
                return JsonResponse({"status": "error", "message": "Taller no encontrado"}, status=400)

            vehiculo_data = {
                'patente': data.get('patente'),
                'marca': data.get('marca'),
                'modelo': data.get('modelo'),
                'anio': data.get('anio'),
                'tipo': data.get('tipo_vehiculo'),
                'estado': 'Disponible',
                'ubicacion': taller_obj  # ← objeto, no string
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
                return JsonResponse({
                    "status": "error",
                    "errors": form.errors
                }, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)



def existe_vehiculo(request):
    patente = request.GET.get('patente')
    existe = Vehiculo.objects.filter(patente=patente).exists()
    return JsonResponse({'existe': existe})
