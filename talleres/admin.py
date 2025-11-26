# talleres/admin.py
from django.contrib import admin
from .models import Recinto, Taller


@admin.register(Recinto)
class RecintoAdmin(admin.ModelAdmin):
    list_display = ("recinto_id", "nombre", "ubicacion", "jefe_recinto")
    search_fields = ("nombre", "ubicacion")
    ordering = ("recinto_id",)


@admin.register(Taller)
class TallerAdmin(admin.ModelAdmin):
    list_display = ("taller_id", "nombre", "ubicacion", "encargado_taller")
    # 'nombre' y 'ubicacion' son propiedades, para search usamos los campos reales:
    search_fields = ("recinto__nombre", "recinto__ubicacion", "encargado_taller")
    list_filter = ("recinto",)
    ordering = ("taller_id",)
