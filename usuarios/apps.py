from django.apps import AppConfig
from django.db.models.signals import post_migrate


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuarios'
    verbose_name = 'Usuarios y seguridad'

    def ready(self):
        # Al terminar "migrate" se crean los roles y se les asignan sus permisos
        from .roles import configurar_roles_despues_de_migrar

        post_migrate.connect(configurar_roles_despues_de_migrar, sender=self)
