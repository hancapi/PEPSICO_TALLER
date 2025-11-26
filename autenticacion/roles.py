# autenticacion/roles.py
from django.contrib.auth.decorators import user_passes_test
from autenticacion.models import Empleado


def has_role(user, roles):
    """
    Verifica si el usuario autenticado pertenece a alguno de los grupos indicados.
    `roles` es una lista de nombres de grupos, ej: ['CHOFER', 'SUPERVISOR'].
    """
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name__in=roles).exists()


# ---- Roles de acuerdo a Casos de Uso ----
chofer_only      = user_passes_test(lambda u: has_role(u, ['CHOFER']))
mecanico_only    = user_passes_test(lambda u: has_role(u, ['MECANICO']))
supervisor_only  = user_passes_test(lambda u: has_role(u, ['SUPERVISOR']))
guardia_only     = user_passes_test(lambda u: has_role(u, ['GUARDIA']))

# 👇 NUEVO: sólo Administrador Web
def _is_admin_web(user):
    if not user or not user.is_authenticated:
        return False

    # 1) Si pertenece al grupo ADMIN_WEB → ok
    if user.groups.filter(name='ADMIN_WEB').exists():
        return True

    # 2) O si tiene el flag es_admin_web en Empleado
    return Empleado.objects.filter(
        usuario=user.username,
        es_admin_web=True
    ).exists()

admin_web_only = user_passes_test(_is_admin_web)

chofer_or_supervisor   = user_passes_test(lambda u: has_role(u, ['CHOFER', 'SUPERVISOR']))
mecanico_or_supervisor = user_passes_test(lambda u: has_role(u, ['MECANICO', 'SUPERVISOR']))

todos_roles = user_passes_test(
    lambda u: has_role(
        u,
        ['CHOFER', 'MECANICO', 'SUPERVISOR', 'ADMINISTRATIVO', 'GUARDIA', 'ADMIN_WEB']
    )
)
