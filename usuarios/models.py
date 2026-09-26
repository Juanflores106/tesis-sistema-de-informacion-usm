"""
Modelos del módulo de Usuarios y seguridad.

Para el inicio de sesión se usa el modelo User que trae Django (usuario,
contraseña cifrada, nombres, correo y estado activo/inactivo). Los roles se
manejan con los Grupos de Django (ver roles.py). Aquí solo se agregan los
datos del trabajador que Django no trae.
"""
from django.conf import settings
from django.db import models

from estudiantes.models import validar_cedula, validar_telefono


class Perfil(models.Model):
    """Datos adicionales del trabajador del colegio que usa el sistema (relación 1 a 1 con User)."""
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil'
    )
    cedula = models.CharField(
        'cédula de identidad', max_length=9, unique=True, validators=[validar_cedula]
    )
    cargo = models.CharField(max_length=80)
    telefono = models.CharField(
        'teléfono', max_length=12, blank=True, validators=[validar_telefono]
    )

    class Meta:
        verbose_name = 'perfil de usuario'
        verbose_name_plural = 'perfiles de usuario'
        ordering = ['usuario__last_name', 'usuario__first_name']

    def __str__(self):
        return f'{self.usuario.get_full_name() or self.usuario.username} ({self.cargo})'
