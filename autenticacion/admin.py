# autenticacion/admin.py
from django.contrib import admin
from autenticacion.models import Empleado


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):

    # ==========================================================================================
    # CAMPOS MOSTRADOS EN LISTA
    # ==========================================================================================
    list_display = (
        'rut',
        'usuario',
        'nombre',
        'cargo',
        'region',
        'recinto',      # antes: 'taller'
        'is_active',
        'is_staff',
        'is_superuser',
        'last_login',
    )

    # Campos que pueden editarse directamente sin entrar al registro
    list_editable = (
        'cargo',
        'region',
        'recinto',      # antes: 'taller'
        'is_active',
    )

    # ==========================================================================================
    # FILTROS LATERALES
    # ==========================================================================================
    list_filter = (
        'cargo',
        'region',
        'recinto',      # antes: 'taller'
        'is_active',
        'is_staff',
        'is_superuser',
    )

    # ==========================================================================================
    # BÚSQUEDA
    # ==========================================================================================
    search_fields = (
        'rut',
        'usuario',
        'nombre',
        'cargo',
    )

    # ==========================================================================================
    # ORDEN
    # ==========================================================================================
    ordering = ('nombre',)

    # ==========================================================================================
    # AGRUPACIÓN DE CAMPOS EN LA FICHA (más profesional)
    # ==========================================================================================
    fieldsets = (
        ("Información Personal", {
            "fields": ("rut", "nombre", "usuario", "password", "cargo", "region", "recinto")
        }),
        ("Permisos", {
            "fields": ("is_active", "is_staff", "is_superuser"),
            "classes": ("collapse",)
        }),
        ("Sesión", {
            "fields": ("last_login",),
            "classes": ("collapse",)
        }),
    )

    readonly_fields = ("last_login",)
