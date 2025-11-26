# ordenestrabajo/admin.py
from django.contrib import admin
from .models import (
    OrdenTrabajo,
    Pausa,
    SolicitudIngresoVehiculo,
    Incidente,
    Llave,
    DesignacionVehicular,
    Repuesto,
    ControlAcceso,
)

# ============================================================
# ORDEN DE TRABAJO
# ============================================================
@admin.register(OrdenTrabajo)
class OrdenTrabajoAdmin(admin.ModelAdmin):
    list_display = (
        'ot_id',
        'patente',
        'recinto',          # antes: 'taller'
        'estado',
        'fecha_ingreso',
        'hora_ingreso',
        'rut',
        'rut_creador',
    )
    list_editable = ('estado',)

    list_filter = ('estado', 'recinto', 'fecha_ingreso')  # antes: 'taller'
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


# ============================================================
# INCIDENTES
# ============================================================
@admin.register(Incidente)
class IncidenteAdmin(admin.ModelAdmin):
    list_display = ("incidente_id", "fecha", "vehiculo", "empleado")
    list_filter = ("fecha",)
    search_fields = ("vehiculo__patente", "empleado__rut", "descripcion")


# ============================================================
# LLAVES
# ============================================================
@admin.register(Llave)
class LlaveAdmin(admin.ModelAdmin):
    list_display = ("llave_id", "vehiculo", "empleado", "estado")
    list_filter = ("estado",)
    search_fields = ("vehiculo__patente", "empleado__rut")


# ============================================================
# DESIGNACIÓN VEHICULAR
# ============================================================
@admin.register(DesignacionVehicular)
class DesignacionVehicularAdmin(admin.ModelAdmin):
    list_display = (
        "prestamo_id",
        "vehiculo",
        "empleado",
        "fecha_inicio",
        "fecha_fin",
        "estado",
    )
    list_filter = ("estado", "fecha_inicio", "fecha_fin")
    search_fields = ("vehiculo__patente", "empleado__rut")


# ============================================================
# REPUESTOS
# ============================================================
@admin.register(Repuesto)
class RepuestoAdmin(admin.ModelAdmin):
    list_display = ("repuesto_id", "nombre", "cantidad", "orden_trabajo")
    search_fields = ("nombre", "orden_trabajo__ot_id")


# ============================================================
# CONTROL DE ACCESO
# ============================================================
@admin.register(ControlAcceso)
class ControlAccesoAdmin(admin.ModelAdmin):
    list_display = (
        "control_id",
        "vehiculo",
        "fecha_ingreso",
        "fecha_salida",
        "guardia_ingreso",
        "guardia_salida",
        "chofer",
    )
    list_filter = ("fecha_ingreso", "fecha_salida")
    search_fields = (
        "vehiculo__patente",
        "guardia_ingreso__rut",
        "guardia_salida__rut",
        "chofer__rut",
    )
