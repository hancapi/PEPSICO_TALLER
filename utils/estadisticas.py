# utils/estadisticas.py
from vehiculos.models import Vehiculo

def contar_vehiculos_por_estado():
    vehiculos = Vehiculo.objects.all()
    return {
        'total': vehiculos.count(),
        'disponibles': vehiculos.filter(estado='Disponible').count(),
        'en_taller': vehiculos.filter(estado='En Taller').count(),
        'en_proceso': vehiculos.filter(estado='En Proceso').count(),
    }
