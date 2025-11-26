# autenticacion/roles.py
from django.contrib.auth.decorators import user_passes_test


def has_role(user, roles):
    """
    Verifica si el usuario autenticado pertenece a alguno de los grupos indicados.
    `roles` es una lista de nombres de grupos, ej: ['CHOFER', 'SUPERVISOR'].
    """
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name__in=roles).exists()


# ---- Roles de acuerdo a Casos de Uso ----
chofer_only    = user_passes_test(lambda u: has_role(u, ['CHOFER']))
mecanico_only  = user_passes_test(lambda u: has_role(u, ['MECANICO']))
supervisor_only = user_passes_test(lambda u: has_role(u, ['SUPERVISOR']))
guardia_only   = user_passes_test(lambda u: has_role(u, ['GUARDIA']))  # 👈 NUEVO

chofer_or_supervisor   = user_passes_test(lambda u: has_role(u, ['CHOFER', 'SUPERVISOR']))
mecanico_or_supervisor = user_passes_test(lambda u: has_role(u, ['MECANICO', 'SUPERVISOR']))

todos_roles = user_passes_test(
    lambda u: has_role(u, ['CHOFER', 'MECANICO', 'SUPERVISOR', 'ADMINISTRATIVO', 'GUARDIA'])  # 👈 incluye GUARDIA
)
