# ordenestrabajo/admin.py
from django.contrib import admin
from .models import (
    OrdenTrabajo,
    Repuesto,
    Incidente,
    PrestamoVehiculo,
    Llave,
    Pausa
)

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
# REPUESTOS
# ============================================================
@admin.register(Repuesto)
class RepuestoAdmin(admin.ModelAdmin):
    list_display = ('repuesto_id', 'ot', 'nombre', 'cantidad')
    search_fields = ('nombre', 'ot__ot_id')
    ordering = ('repuesto_id',)


# ============================================================
# INCIDENTES
# ============================================================
@admin.register(Incidente)
class IncidenteAdmin(admin.ModelAdmin):
    list_display = ('incidente_id', 'patente', 'rut', 'fecha')
    list_filter = ('fecha', 'patente')
    search_fields = ('incidente_id', 'patente__patente', 'rut__rut')
    ordering = ('-fecha',)


# ============================================================
# PRESTAMOS
# ============================================================
@admin.register(PrestamoVehiculo)
class PrestamoVehiculoAdmin(admin.ModelAdmin):
    list_display = (
        "prestamo_id",
        "patente",
        "empleados_rut",
        "estado",
        "fecha_inicio",
        "fecha_fin"
    )
    list_editable = ("estado",)
    list_filter = ("estado", "fecha_inicio")
    search_fields = ("patente__patente", "empleados_rut__rut")
    ordering = ("-fecha_inicio",)


# ============================================================
# LLAVES
# ============================================================
@admin.register(Llave)
class LlaveAdmin(admin.ModelAdmin):
    list_display = ("llave_id", "patente", "estado", "rut")
    list_editable = ("estado",)
    list_filter = ("estado",)
    search_fields = ("patente__patente", "rut__rut")
    ordering = ("llave_id",)


# ============================================================
# PAUSAS
# ============================================================
@admin.register(Pausa)
class PausaAdmin(admin.ModelAdmin):
    list_display = ('id', 'ot', 'motivo', 'inicio', 'fin', 'activo')
    list_filter = ('activo', 'inicio', 'fin')
    search_fields = ('ot__ot_id', 'motivo', 'observacion')
    ordering = ('-inicio',)
