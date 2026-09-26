"""
Pruebas unitarias del módulo de Usuarios y seguridad.

Ejecutar con:  python manage.py test usuarios
Django crea una base de datos temporal (test_colegio_marycarmen), ejecuta
las pruebas y la elimina al terminar; los datos reales no se tocan.
"""
from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from .models import Perfil
from .roles import ADMINISTRACION, CONTROL_ESTUDIOS, DIRECTOR, ROLES, rol_de

CLAVE = 'Marycarmen.2026'


def crear_usuario(username, rol=None, **datos):
    """Crea un usuario de prueba y, si se indica, le asigna un rol."""
    usuario = User.objects.create_user(username=username, password=CLAVE, **datos)
    if rol:
        usuario.groups.add(Group.objects.get(name=rol))
    return usuario


# ---------------------------------------------------------------------------
# Roles y permisos
# ---------------------------------------------------------------------------
class RolesTests(TestCase):
    def test_los_tres_roles_se_crean_al_migrar(self):
        nombres = set(Group.objects.values_list('name', flat=True))
        self.assertTrue(set(ROLES).issubset(nombres))

    def test_ningun_rol_puede_eliminar_estudiantes_ni_representantes(self):
        for numero, rol in enumerate(ROLES):
            usuario = crear_usuario(f'usuario{numero}', rol)
            self.assertFalse(usuario.has_perm('estudiantes.delete_estudiante'), rol)
            self.assertFalse(usuario.has_perm('estudiantes.delete_representante'), rol)

    def test_control_estudios_gestiona_estudiantes_pero_no_usuarios(self):
        usuario = crear_usuario('secretaria', CONTROL_ESTUDIOS)
        self.assertTrue(usuario.has_perm('estudiantes.add_estudiante'))
        self.assertTrue(usuario.has_perm('estudiantes.change_representante'))
        self.assertFalse(usuario.has_perm('auth.add_user'))

    def test_administracion_solo_consulta_estudiantes(self):
        usuario = crear_usuario('cobranzas', ADMINISTRACION)
        self.assertTrue(usuario.has_perm('estudiantes.view_estudiante'))
        self.assertFalse(usuario.has_perm('estudiantes.add_estudiante'))
        self.assertFalse(usuario.has_perm('estudiantes.change_estudiante'))

    def test_director_administra_usuarios(self):
        usuario = crear_usuario('director', DIRECTOR)
        self.assertTrue(usuario.has_perm('auth.add_user'))
        self.assertTrue(usuario.has_perm('auth.change_user'))
        self.assertFalse(usuario.has_perm('auth.delete_user'))

    def test_nombre_del_rol(self):
        self.assertEqual(rol_de(crear_usuario('director', DIRECTOR)), DIRECTOR)
        self.assertEqual(rol_de(crear_usuario('nuevo')), 'Sin rol asignado')
        admin = User.objects.create_superuser('soporte', password=CLAVE)
        self.assertEqual(rol_de(admin), 'Administrador del sistema')


# ---------------------------------------------------------------------------
# Inicio y cierre de sesión
# ---------------------------------------------------------------------------
class SesionTests(TestCase):
    def setUp(self):
        self.usuario = crear_usuario('secretaria', CONTROL_ESTUDIOS, first_name='María')

    def test_pagina_de_inicio_de_sesion_carga(self):
        respuesta = self.client.get(reverse('usuarios:login'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Iniciar sesión')

    def test_datos_correctos_llevan_al_inicio(self):
        respuesta = self.client.post(
            reverse('usuarios:login'), {'username': 'secretaria', 'password': CLAVE}
        )
        self.assertRedirects(respuesta, reverse('inicio'))

    def test_clave_incorrecta_muestra_error(self):
        respuesta = self.client.post(
            reverse('usuarios:login'), {'username': 'secretaria', 'password': 'otra'}
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context['form'].errors)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_usuario_desactivado_no_puede_entrar(self):
        self.usuario.is_active = False
        self.usuario.save()
        self.client.post(reverse('usuarios:login'), {'username': 'secretaria', 'password': CLAVE})
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_sin_sesion_se_redirige_al_login(self):
        respuesta = self.client.get(reverse('inicio'))
        self.assertRedirects(respuesta, f"{reverse('usuarios:login')}?next=/")

    def test_cerrar_sesion(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.post(reverse('usuarios:logout'))
        self.assertRedirects(respuesta, reverse('usuarios:login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_cambiar_clave_propia(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.post(reverse('usuarios:cambiar_clave'), {
            'old_password': CLAVE,
            'new_password1': 'NuevaClave.2026',
            'new_password2': 'NuevaClave.2026',
        })
        self.assertRedirects(respuesta, reverse('inicio'))
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('NuevaClave.2026'))


# ---------------------------------------------------------------------------
# Menú según el rol
# ---------------------------------------------------------------------------
def enlace(nombre_url):
    """Texto exacto del enlace en la página (evita confundir /usuarios/ con /usuarios/cambiar-clave/)."""
    return f'href="{reverse(nombre_url)}"'


class MenuPorRolTests(TestCase):
    def test_control_estudios_ve_estudiantes_y_no_usuarios(self):
        self.client.force_login(crear_usuario('secretaria', CONTROL_ESTUDIOS))
        respuesta = self.client.get(reverse('inicio'))
        self.assertContains(respuesta, enlace('estudiantes:estudiante_lista'))
        self.assertContains(respuesta, enlace('estudiantes:estudiante_crear'))
        self.assertNotContains(respuesta, enlace('usuarios:lista'))

    def test_administracion_consulta_estudiantes_sin_opcion_de_registrar(self):
        self.client.force_login(crear_usuario('cobranzas', ADMINISTRACION))
        respuesta = self.client.get(reverse('inicio'))
        self.assertContains(respuesta, enlace('estudiantes:estudiante_lista'))
        self.assertNotContains(respuesta, enlace('estudiantes:estudiante_crear'))
        self.assertNotContains(respuesta, enlace('usuarios:lista'))

    def test_director_ve_todas_las_opciones(self):
        self.client.force_login(crear_usuario('director', DIRECTOR))
        respuesta = self.client.get(reverse('inicio'))
        self.assertContains(respuesta, enlace('estudiantes:estudiante_lista'))
        self.assertContains(respuesta, enlace('usuarios:lista'))


# ---------------------------------------------------------------------------
# Administración de usuarios (Director)
# ---------------------------------------------------------------------------
class GestionUsuariosTests(TestCase):
    def setUp(self):
        self.director = crear_usuario('director', DIRECTOR)
        self.client.force_login(self.director)

    def datos_usuario(self, **cambios):
        datos = {
            'first_name': 'Ana',
            'last_name': 'Rodríguez',
            'cedula': '15123456',
            'cargo': 'Secretaria',
            'telefono': '0414-1234567',
            'email': 'ana@example.com',
            'rol': Group.objects.get(name=CONTROL_ESTUDIOS).pk,
            'username': 'arodriguez',
            'password1': 'Secretaria.2026',
            'password2': 'Secretaria.2026',
        }
        datos.update(cambios)
        return datos

    def test_director_ve_la_lista_de_usuarios(self):
        respuesta = self.client.get(reverse('usuarios:lista'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'director')

    def test_otros_roles_reciben_acceso_denegado(self):
        self.client.force_login(crear_usuario('secretaria', CONTROL_ESTUDIOS))
        self.assertEqual(self.client.get(reverse('usuarios:lista')).status_code, 403)
        self.assertEqual(self.client.get(reverse('usuarios:crear')).status_code, 403)

    def test_registrar_usuario_con_rol_y_perfil(self):
        respuesta = self.client.post(reverse('usuarios:crear'), self.datos_usuario())
        self.assertRedirects(respuesta, reverse('usuarios:lista'))
        usuario = User.objects.get(username='arodriguez')
        self.assertTrue(usuario.groups.filter(name=CONTROL_ESTUDIOS).exists())
        self.assertEqual(usuario.perfil.cedula, '15123456')
        self.assertTrue(usuario.check_password('Secretaria.2026'))

    def test_cedula_repetida_es_rechazada(self):
        self.client.post(reverse('usuarios:crear'), self.datos_usuario())
        respuesta = self.client.post(
            reverse('usuarios:crear'), self.datos_usuario(username='otro')
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('cedula', respuesta.context['form'].errors)
        self.assertFalse(User.objects.filter(username='otro').exists())

    def test_modificar_rol_de_un_usuario(self):
        usuario = crear_usuario('empleado', CONTROL_ESTUDIOS)
        datos = self.datos_usuario(username='empleado', rol=Group.objects.get(name=ADMINISTRACION).pk)
        respuesta = self.client.post(reverse('usuarios:editar', args=[usuario.pk]), datos)
        self.assertRedirects(respuesta, reverse('usuarios:lista'))
        self.assertEqual(rol_de(usuario), ADMINISTRACION)
        self.assertEqual(Perfil.objects.get(usuario=usuario).cargo, 'Secretaria')

    def test_director_no_puede_cambiar_su_propio_rol(self):
        datos = self.datos_usuario(username='director', rol=Group.objects.get(name=ADMINISTRACION).pk)
        self.client.post(reverse('usuarios:editar', args=[self.director.pk]), datos)
        self.assertEqual(rol_de(self.director), DIRECTOR)

    def test_desactivar_y_activar_usuario(self):
        usuario = crear_usuario('empleado', CONTROL_ESTUDIOS)
        self.client.post(reverse('usuarios:cambiar_estado', args=[usuario.pk]))
        usuario.refresh_from_db()
        self.assertFalse(usuario.is_active)
        self.client.post(reverse('usuarios:cambiar_estado', args=[usuario.pk]))
        usuario.refresh_from_db()
        self.assertTrue(usuario.is_active)

    def test_director_no_puede_desactivarse_a_si_mismo(self):
        self.client.post(reverse('usuarios:cambiar_estado', args=[self.director.pk]))
        self.director.refresh_from_db()
        self.assertTrue(self.director.is_active)

    def test_asignar_nueva_clave(self):
        usuario = crear_usuario('empleado', CONTROL_ESTUDIOS)
        respuesta = self.client.post(
            reverse('usuarios:establecer_clave', args=[usuario.pk]),
            {'new_password1': 'Temporal.2026', 'new_password2': 'Temporal.2026'},
        )
        self.assertRedirects(respuesta, reverse('usuarios:lista'))
        usuario.refresh_from_db()
        self.assertTrue(usuario.check_password('Temporal.2026'))

    def test_superusuario_no_es_visible_para_el_director(self):
        soporte = User.objects.create_superuser('soporte', password=CLAVE)
        respuesta = self.client.get(reverse('usuarios:lista'))
        self.assertNotContains(respuesta, 'soporte')
        respuesta = self.client.get(reverse('usuarios:editar', args=[soporte.pk]))
        self.assertEqual(respuesta.status_code, 404)
