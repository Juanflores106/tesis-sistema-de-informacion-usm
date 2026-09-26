"""
Procesador de contexto: agrega el rol del usuario a todas las plantillas
para mostrarlo en el encabezado.
"""
from .roles import rol_de


def rol_usuario(request):
    return {'rol_usuario': rol_de(request.user)}
