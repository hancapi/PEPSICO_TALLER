# autenticacion/admin.py
from django.contrib import admin
from django.contrib.auth.models import Group
from autenticacion.models import Empleado


class AdminWebFilter(admin.SimpleListFilter):
    """
    Filtro lateral para ver sólo empleados que son / no son Admin Web.
    Basado en el grupo ADMIN_WEB del User asociado.
    """
    title = "Admin Web"
    parameter_name = "admin_web"

    def lookups(self, request, model_admin):
        return (
            ("si", "Sí"),
            ("no", "No"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset

        # RUTs cuyos usuarios pertenecen al grupo ADMIN_WEB
        admin_group, _ = Group.objects.get_or_create(name="ADMIN_WEB")
        admin_users = admin_group.user_set.values_list("username", flat=True)

        if value == "si":
            return queryset.filter(usuario__in=admin_users)
        if value == "no":
            return queryset.exclude(usuario__in=admin_users)
        return queryset


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
        'recinto',
        'es_admin_web_flag',   # 👈 columna calculada
        'is_active',
        'is_staff',
        'is_superuser',
        'last_login',
    )

    # Campos que pueden editarse directamente sin entrar al registro
    list_editable = (
        'cargo',
        'region',
        'recinto',
        'is_active',
    )

    # ==========================================================================================
    # FILTROS LATERALES
    # ==========================================================================================
    list_filter = (
        'cargo',
        'region',
        'recinto',
        AdminWebFilter,   # 👈 nuevo filtro
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
    # AGRUPACIÓN DE CAMPOS EN LA FICHA
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

    # ==========================================================================================
    # COLUMNAS CALCULADAS
    # ==========================================================================================
    def es_admin_web_flag(self, obj):
        """Muestra Sí/No en base al grupo ADMIN_WEB (propiedad is_admin_web)."""
        return obj.is_admin_web

    es_admin_web_flag.boolean = True
    es_admin_web_flag.short_description = "Admin Web"
