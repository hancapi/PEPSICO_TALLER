# common/decorators.py
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect

def role_required(roles_permitidos):
    """
    Decorador que restringe acceso a usuarios que NO pertenezcan
    a los grupos (roles) definidos en roles_permitidos.
    """
    def check_role(user):
        if not user.is_authenticated:
            return False
        user_groups = user.groups.values_list('name', flat=True)
        return any(role in user_groups for role in roles_permitidos)

    return user_passes_test(
        check_role,
        login_url='inicio-sesion'
    )

