from django import template
from vehiculos.models import Vehiculo

register = template.Library()

@register.simple_tag
def vehiculo_model():
    """
    Devuelve la clase Vehiculo para acceder a sus CHOICES desde templates.
    Uso en template:
        {% vehiculo_model as Vehiculo %}
        {{ Vehiculo.ESTADO_CHOICES }}
    """
    return Vehiculo
