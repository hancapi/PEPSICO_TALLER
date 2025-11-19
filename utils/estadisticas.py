# utils/estadisticas.py
from vehiculos.models import Vehiculo
from autenticacion.models import Empleado

def contar_vehiculos_por_estado():
    """
    Devuelve KPIs globales de vehículos:
    - Total registrados
    - En taller
    - En proceso
    - Disponibles
    """
    vehiculos = Vehiculo.objects.all()
    return {
        'total': vehiculos.count(),
        'en_taller': vehiculos.filter(estado__iexact='En Taller').count(),
        'en_proceso': vehiculos.filter(estado__iexact='En Proceso').count(),
        'disponibles': vehiculos.filter(estado__iexact='Disponible').count(),
    }


def contar_empleados_activos():
    """
    Devuelve la cantidad de empleados activos (solo para supervisores).
    """
    return Empleado.objects.filter(is_active=True).count()
