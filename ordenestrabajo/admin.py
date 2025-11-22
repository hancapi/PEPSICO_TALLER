# ordenestrabajo/admin.py
from django.contrib import admin
from .models import OrdenTrabajo, Pausa, SolicitudIngresoVehiculo

# ============================================================
# ORDEN DE TRABAJO
# ============================================================
@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    list_display = (
        'ot_id',
        'patente',
        'taller',
        'estado',
        'fecha_ingreso',
        'hora_ingreso',
        'rut',
        'rut_creador',
    )
    list_editable = ('estado',)

    list_filter = ('estado', 'taller', 'fecha_ingreso')
    search_fields = (
        'ot_id',
        'patente__patente',
        'rut__rut',
        'rut_creador__rut'
    )
    ordering = ('-fecha_ingreso', '-hora_ingreso')


# ============================================================
# PAUSAS
# ============================================================
@admin.register(Pausa)
class PausaAdmin(admin.ModelAdmin):
    list_display = ('id', 'ot', 'motivo', 'inicio', 'fin', 'activo')
    list_filter = ('activo', 'inicio', 'fin')
    search_fields = ('ot__ot_id', 'motivo', 'observacion')
    ordering = ('-inicio',)


# ============================================================
# SOLICITUDES DE INGRESO DE VEHÍCULOS
# ============================================================
@admin.register(SolicitudIngresoVehiculo)
class SolicitudIngresoVehiculoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "vehiculo",
        "chofer",
        "taller",
        "fecha_solicitada",
        "estado",
        "creado_en",
    )
    list_filter = ("estado", "taller", "fecha_solicitada")
    search_fields = ("vehiculo__patente", "chofer__nombre", "chofer__rut")
    ordering = ("-creado_en",)
