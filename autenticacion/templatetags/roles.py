# autenticacion/templatetags/roles.py
from django import template

register = template.Library()


@register.filter
def has_group(user, group_name):
    """
    Verifica si el usuario pertenece a un grupo Django específico.
    Uso en template:
        {% if request.user|has_group:"SUPERVISOR" %}
    """
    if not user or not user.is_authenticated:
        return False
    if not group_name:
        return False
    return user.groups.filter(name__iexact=group_name.strip()).exists()


@register.filter
def has_any_group(user, group_names):
    """
    Verifica si el usuario pertenece a cualquiera de los grupos indicados.
    Uso en template:
        {% if request.user|has_any_group:"SUPERVISOR,MECANICO" %}
    """
    if not user or not user.is_authenticated:
        return False

    if not group_names:
        return False

    names = [g.strip() for g in group_names.split(',') if g.strip()]
    if not names:
        return False

    return user.groups.filter(name__in=names).exists()


@register.filter
def has_role(user, role_name):
    """
    Alias semántico de has_group, para usar 'rol' == grupo.
    Uso:
        {% if request.user|has_role:"SUPERVISOR" %}
    """
    return has_group(user, role_name)


@register.filter
def has_any_role(user, roles):
    """
    Alias semántico de has_any_group.
    Uso:
        {% if request.user|has_any_role:"SUPERVISOR,CHOFER" %}
    """
    return has_any_group(user, roles)
