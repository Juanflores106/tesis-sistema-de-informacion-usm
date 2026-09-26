"""
Etiquetas de plantilla de uso general en la interfaz.
Uso en una plantilla:  {% load interfaz %}
"""
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def url_pagina(context, numero):
    """
    Enlace a otra página de un listado conservando la búsqueda y los filtros
    que el usuario ya aplicó (por ejemplo ?q=perez&estatus=ACTIVO&page=2).
    """
    parametros = context['request'].GET.copy()
    parametros['page'] = numero
    return '?' + parametros.urlencode()
