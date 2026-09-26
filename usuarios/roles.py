"""
Roles del sistema y su matriz de permisos.

Cada rol es un Grupo (Group) de Django. Los permisos de cada grupo se asignan
automáticamente según MATRIZ_PERMISOS cada vez que se ejecuta:
    python manage.py migrate

Para cambiar lo que puede hacer un rol, se modifica la matriz y se vuelve a
ejecutar migrate. Las vistas del sistema verifican estos permisos, por lo que
un usuario solo ve y usa las opciones de su rol.
"""
from django.apps import apps
from django.contrib.auth.management import create_permissions
from django.contrib.auth.models import Group, Permission
from django.db.models import Q

# ---------------------------------------------------------------------------
# Nombres de los roles
# ---------------------------------------------------------------------------
DIRECTOR = 'Director'
CONTROL_ESTUDIOS = 'Control de Estudios'
ADMINISTRACION = 'Administración'

ROLES = (DIRECTOR, CONTROL_ESTUDIOS, ADMINISTRACION)

# ---------------------------------------------------------------------------
# Acciones sobre los datos (prefijos de los permisos de Django):
#   view = consultar, add = registrar, change = modificar, delete = eliminar.
# "delete" no se asigna sobre los datos principales: los registros no se
# borran, se cambia su estatus. Solo se permite en tablas intermedias, donde
# eliminar significa deshacer un vínculo (por ejemplo, quitar un representante
# asignado por error), sin borrar a las personas.
# ---------------------------------------------------------------------------
CONSULTAR = ('view',)
GESTIONAR = ('view', 'add', 'change')
GESTIONAR_VINCULO = ('view', 'add', 'change', 'delete')

# Clave: 'app' (todos los modelos de la app) o 'app.modelo' (un solo modelo).
MATRIZ_PERMISOS = {
    DIRECTOR: {
        'auth.user': GESTIONAR,
        'usuarios': GESTIONAR,
        'estudiantes': GESTIONAR,
        'estudiantes.estudianterepresentante': GESTIONAR_VINCULO,
        'academico': GESTIONAR,
        'inscripciones': GESTIONAR,
        'finanzas': GESTIONAR,
    },
    CONTROL_ESTUDIOS: {
        'estudiantes': GESTIONAR,
        'estudiantes.estudianterepresentante': GESTIONAR_VINCULO,
        'academico': GESTIONAR,
        'inscripciones': GESTIONAR,
    },
    ADMINISTRACION: {
        'estudiantes': CONSULTAR,
        'inscripciones': CONSULTAR,
        'finanzas': GESTIONAR,
    },
}


def permisos_del_rol(rol):
    """Devuelve los permisos (Permission) que le corresponden a un rol según la matriz."""
    filtro = Q(pk__in=[])
    for app_modelo, acciones in MATRIZ_PERMISOS[rol].items():
        app_label, _, modelo = app_modelo.partition('.')
        condicion = Q(content_type__app_label=app_label)
        if modelo:
            condicion &= Q(content_type__model=modelo)
        prefijos = Q(pk__in=[])
        for accion in acciones:
            prefijos |= Q(codename__startswith=f'{accion}_')
        filtro |= condicion & prefijos
    return Permission.objects.filter(filtro)


def configurar_roles():
    """Crea los grupos de los roles (si no existen) y les asigna sus permisos."""
    for rol in ROLES:
        grupo, _ = Group.objects.get_or_create(name=rol)
        grupo.permissions.set(permisos_del_rol(rol))


def configurar_roles_despues_de_migrar(sender, using='default', **kwargs):
    """
    Se ejecuta automáticamente al final de "python manage.py migrate".
    Primero se asegura de que existan los permisos de TODAS las apps
    (Django los crea app por app) y luego configura los roles.
    """
    for app_config in apps.get_app_configs():
        create_permissions(app_config, verbosity=0, using=using)
    configurar_roles()


def rol_de(usuario):
    """Nombre del rol del usuario, para mostrarlo en pantalla."""
    if not usuario.is_authenticated:
        return ''
    if usuario.is_superuser:
        return 'Administrador del sistema'
    grupo = usuario.groups.filter(name__in=ROLES).first()
    return grupo.name if grupo else 'Sin rol asignado'
