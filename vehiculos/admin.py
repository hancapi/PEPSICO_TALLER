# vehiculos/admin.py
from django.contrib import admin
from .models import Vehiculo


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = (
        'patente',
        'marca',
        'modelo',
        'anio',
        'tipo',
        'estado',
        'ubicacion',
    )

    list_editable = (
        'tipo',
        'estado',
        'ubicacion',
    )

    search_fields = (
        'patente',
        'marca',
        'modelo',
        'tipo',
        'ubicacion',
    )

    list_filter = (
        'estado',
        'tipo',
        'ubicacion',
        'anio',
    )

    ordering = ('patente',)
