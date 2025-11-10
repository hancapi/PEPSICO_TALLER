# autenticacion/admin.py
from django.contrib import admin
from autenticacion.models import Empleado, Taller

@admin.register(Taller)
class TallerAdmin(admin.ModelAdmin):
    list_display = ('taller_id', 'nombre', 'ubicacion', 'encargado_taller')
    search_fields = ('nombre', 'ubicacion')

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('rut', 'usuario', 'nombre', 'cargo', 'taller', 'is_active', 'is_staff', 'is_superuser', 'last_login')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'taller')
    search_fields = ('rut', 'usuario', 'nombre', 'cargo')
