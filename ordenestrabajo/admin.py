# ordenestrabajo/admin.py
from django.contrib import admin
from .models import OrdenTrabajo, Repuesto, Incidente, PrestamoVehiculo, Llave, Pausa

@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    list_display = ('ot_id', 'patente', 'taller', 'rut', 'estado', 'fecha_ingreso', 'fecha_salida')
    list_filter = ('estado', 'taller', 'fecha_ingreso', 'fecha_salida')
    search_fields = ('ot_id', 'patente__patente', 'rut__rut', 'descripcion')

@admin.register(Repuesto)
class RepuestoAdmin(admin.ModelAdmin):
    list_display = ('repuesto_id', 'ot', 'nombre', 'cantidad')
    search_fields = ('nombre', 'ot__ot_id')

@admin.register(Incidente)
class IncidenteAdmin(admin.ModelAdmin):
    list_display = ('incidente_id', 'patente', 'rut', 'fecha')
    list_filter = ('fecha',)

@admin.register(PrestamoVehiculo)
class PrestamoVehiculoAdmin(admin.ModelAdmin):
    list_display = ('prestamo_id', 'patente', 'empleados_rut', 'estado', 'fecha_inicio', 'fecha_fin')
    list_filter = ('estado',)

@admin.register(Llave)
class LlaveAdmin(admin.ModelAdmin):
    list_display = ('llave_id', 'patente', 'rut', 'estado')
    list_filter = ('estado',)

@admin.register(Pausa)
class PausaAdmin(admin.ModelAdmin):
    list_display = ('id', 'ot', 'motivo', 'inicio', 'fin', 'activo')
    list_filter = ('activo', 'inicio', 'fin')
    search_fields = ('ot__ot_id', 'motivo', 'observacion')
