"""
Pruebas unitarias del módulo de Estudiantes y Representantes.

Ejecutar con:  python manage.py test estudiantes
"""
from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from usuarios.roles import ADMINISTRACION, CONTROL_ESTUDIOS
from usuarios.tests import crear_usuario

from .models import Estudiante, EstudianteRepresentante, Representante


def crear_representante(cedula='12345678', **datos):
    valores = {
        'nombres': 'Carmen',
        'apellidos': 'González',
        'sexo': 'F',
        'direccion': 'Av. Municipal, Puerto La Cruz',
        'telefono_principal': '0414-1234567',
    }
    valores.update(datos)
    return Representante.objects.create(cedula=cedula, **valores)


def crear_estudiante(cedula_escolar='11512345678', **datos):
    valores = {
        'nombres': 'Luis',
        'apellidos': 'González',
        'sexo': 'M',
        'direccion': 'Av. Municipal, Puerto La Cruz',
        'fecha_nacimiento': date(2015, 3, 10),
        'lugar_nacimiento': 'Puerto La Cruz',
    }
    valores.update(datos)
    return Estudiante.objects.create(cedula_escolar=cedula_escolar, **valores)


# ---------------------------------------------------------------------------
# Modelos: validaciones y reglas de negocio
# ---------------------------------------------------------------------------
class ModelosTests(TestCase):
    def test_cedula_con_letras_es_invalida(self):
        representante = Representante(
            cedula='12A45678', nombres='A', apellidos='B', sexo='F',
            direccion='X', telefono_principal='0414-1234567',
        )
        with self.assertRaises(ValidationError) as error:
            representante.full_clean()
        self.assertIn('cedula', error.exception.message_dict)

    def test_cedula_muy_corta_es_invalida(self):
        representante = Representante(
            cedula='12345', nombres='A', apellidos='B', sexo='F',
            direccion='X', telefono_principal='0414-1234567',
        )
        with self.assertRaises(ValidationError) as error:
            representante.full_clean()
        self.assertIn('cedula', error.exception.message_dict)

    def test_telefono_con_formato_incorrecto_es_invalido(self):
        representante = Representante(
            cedula='12345678', nombres='A', apellidos='B', sexo='F',
            direccion='X', telefono_principal='414-12345',
        )
        with self.assertRaises(ValidationError) as error:
            representante.full_clean()
        self.assertIn('telefono_principal', error.exception.message_dict)

    def test_varios_estudiantes_sin_cedula_de_identidad(self):
        # La cédula vacía se guarda como NULL, que no choca con la restricción "unique"
        primero = crear_estudiante('A001', cedula='')
        segundo = crear_estudiante('A002', cedula='')
        self.assertIsNone(primero.cedula)
        self.assertIsNone(segundo.cedula)

    def test_cedula_escolar_repetida_no_se_permite(self):
        crear_estudiante('A001')
        with self.assertRaises(IntegrityError), transaction.atomic():
            crear_estudiante('A001')

    def test_texto_y_nombre_completo(self):
        estudiante = crear_estudiante('A001')
        self.assertEqual(estudiante.nombre_completo, 'Luis González')
        self.assertEqual(str(estudiante), 'A001 | Luis González')
        self.assertEqual(str(crear_representante()), 'V-12345678 | Carmen González')

    def test_solo_un_representante_legal_por_estudiante(self):
        estudiante = crear_estudiante()
        EstudianteRepresentante.objects.create(
            estudiante=estudiante, representante=crear_representante('11111111'),
            parentesco='MADRE', es_representante_legal=True,
        )
        segundo = EstudianteRepresentante(
            estudiante=estudiante, representante=crear_representante('22222222'),
            parentesco='PADRE', es_representante_legal=True,
        )
        with self.assertRaises(ValidationError):
            segundo.full_clean()

    def test_mismo_representante_no_se_asigna_dos_veces(self):
        estudiante = crear_estudiante()
        representante = crear_representante()
        EstudianteRepresentante.objects.create(
            estudiante=estudiante, representante=representante, parentesco='MADRE'
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            EstudianteRepresentante.objects.create(
                estudiante=estudiante, representante=representante, parentesco='OTRO'
            )

    def test_representante_legal(self):
        estudiante = crear_estudiante()
        self.assertIsNone(estudiante.representante_legal)
        madre = crear_representante()
        EstudianteRepresentante.objects.create(
            estudiante=estudiante, representante=madre,
            parentesco='MADRE', es_representante_legal=True,
        )
        self.assertEqual(estudiante.representante_legal, madre)

    def test_no_se_borra_un_representante_con_estudiantes(self):
        representante = crear_representante()
        EstudianteRepresentante.objects.create(
            estudiante=crear_estudiante(), representante=representante, parentesco='MADRE'
        )
        with self.assertRaises(ProtectedError):
            representante.delete()


# ---------------------------------------------------------------------------
# Pantallas de estudiantes
# ---------------------------------------------------------------------------
class EstudianteVistasTests(TestCase):
    def setUp(self):
        self.secretaria = crear_usuario('secretaria', CONTROL_ESTUDIOS)
        self.client.force_login(self.secretaria)

    def datos_estudiante(self, **cambios):
        datos = {
            'nacionalidad': 'V',
            'cedula_escolar': '11512345678',
            'cedula': '',
            'nombres': 'Luis',
            'apellidos': 'González',
            'sexo': 'M',
            'fecha_nacimiento': '2015-03-10',
            'lugar_nacimiento': 'Puerto La Cruz',
            'direccion': 'Av. Municipal',
            'condiciones_medicas': '',
        }
        datos.update(cambios)
        return datos

    def test_registrar_estudiante(self):
        respuesta = self.client.post(reverse('estudiantes:estudiante_crear'), self.datos_estudiante())
        estudiante = Estudiante.objects.get(cedula_escolar='11512345678')
        self.assertRedirects(respuesta, reverse('estudiantes:estudiante_detalle', args=[estudiante.pk]))
        self.assertEqual(estudiante.estatus, Estudiante.Estatus.ACTIVO)
        self.assertIsNone(estudiante.cedula)

    def test_fecha_de_nacimiento_futura_es_rechazada(self):
        manana = (date.today() + timedelta(days=2)).isoformat()
        respuesta = self.client.post(
            reverse('estudiantes:estudiante_crear'), self.datos_estudiante(fecha_nacimiento=manana)
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('fecha_nacimiento', respuesta.context['form'].errors)

    def test_cedula_escolar_repetida_muestra_error(self):
        crear_estudiante('11512345678')
        respuesta = self.client.post(reverse('estudiantes:estudiante_crear'), self.datos_estudiante())
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('cedula_escolar', respuesta.context['form'].errors)

    def test_retirar_estudiante_cambia_estatus_sin_borrarlo(self):
        estudiante = crear_estudiante()
        respuesta = self.client.post(
            reverse('estudiantes:estudiante_editar', args=[estudiante.pk]),
            self.datos_estudiante(estatus='RETIRADO'),
        )
        self.assertRedirects(respuesta, reverse('estudiantes:estudiante_detalle', args=[estudiante.pk]))
        estudiante.refresh_from_db()
        self.assertEqual(estudiante.estatus, Estudiante.Estatus.RETIRADO)

    def test_busqueda_y_filtro_por_estatus(self):
        crear_estudiante('A001', nombres='Ana', apellidos='Pérez')
        crear_estudiante('A002', nombres='José', apellidos='Marcano', estatus='RETIRADO')
        url = reverse('estudiantes:estudiante_lista')
        self.assertEqual(list(self.client.get(url, {'q': 'pérez'}).context['estudiantes']),
                         list(Estudiante.objects.filter(cedula_escolar='A001')))
        self.assertEqual(list(self.client.get(url, {'estatus': 'RETIRADO'}).context['estudiantes']),
                         list(Estudiante.objects.filter(cedula_escolar='A002')))

    def test_ficha_del_estudiante(self):
        estudiante = crear_estudiante(condiciones_medicas='Alergia a la penicilina')
        respuesta = self.client.get(reverse('estudiantes:estudiante_detalle', args=[estudiante.pk]))
        self.assertContains(respuesta, 'Alergia a la penicilina')
        self.assertContains(respuesta, 'no tiene representante legal')

    def test_administracion_consulta_pero_no_registra_ni_modifica(self):
        estudiante = crear_estudiante()
        self.client.force_login(crear_usuario('cobranzas', ADMINISTRACION))
        self.assertEqual(self.client.get(reverse('estudiantes:estudiante_lista')).status_code, 200)
        self.assertEqual(self.client.get(reverse('estudiantes:estudiante_crear')).status_code, 403)
        self.assertEqual(
            self.client.get(reverse('estudiantes:estudiante_editar', args=[estudiante.pk])).status_code, 403
        )

    def test_usuario_sin_sesion_es_enviado_al_login(self):
        self.client.logout()
        url = reverse('estudiantes:estudiante_lista')
        respuesta = self.client.get(url)
        self.assertRedirects(respuesta, f"{reverse('usuarios:login')}?next={url}")


# ---------------------------------------------------------------------------
# Pantallas de representantes y asignación a estudiantes
# ---------------------------------------------------------------------------
class RepresentanteVistasTests(TestCase):
    def setUp(self):
        self.client.force_login(crear_usuario('secretaria', CONTROL_ESTUDIOS))
        self.estudiante = crear_estudiante()
        self.madre = crear_representante('12345678')

    def datos_representante(self, **cambios):
        datos = {
            'nacionalidad': 'V',
            'cedula': '87654321',
            'nombres': 'Pedro',
            'apellidos': 'González',
            'sexo': 'M',
            'fecha_nacimiento': '1985-05-20',
            'telefono_principal': '0424-7654321',
            'telefono_secundario': '',
            'correo': '',
            'ocupacion': '',
            'lugar_trabajo': '',
            'direccion': 'Av. Municipal',
        }
        datos.update(cambios)
        return datos

    def test_registrar_representante(self):
        respuesta = self.client.post(reverse('estudiantes:representante_crear'), self.datos_representante())
        representante = Representante.objects.get(cedula='87654321')
        self.assertRedirects(
            respuesta, reverse('estudiantes:representante_detalle', args=[representante.pk])
        )

    def test_registrar_representante_y_volver_a_la_pantalla_anterior(self):
        url_asignar = reverse('estudiantes:relacion_crear', args=[self.estudiante.pk])
        respuesta = self.client.post(
            reverse('estudiantes:representante_crear'), self.datos_representante(next=url_asignar)
        )
        self.assertRedirects(respuesta, url_asignar)

    def test_no_redirige_a_sitios_externos(self):
        respuesta = self.client.post(
            reverse('estudiantes:representante_crear'),
            self.datos_representante(next='https://sitio-malicioso.com/'),
        )
        representante = Representante.objects.get(cedula='87654321')
        self.assertRedirects(
            respuesta, reverse('estudiantes:representante_detalle', args=[representante.pk])
        )

    def test_asignar_representante_por_cedula(self):
        respuesta = self.client.post(
            reverse('estudiantes:relacion_crear', args=[self.estudiante.pk]),
            {'cedula_representante': '12345678', 'parentesco': 'MADRE',
             'es_representante_legal': 'on', 'autorizado_retirar': 'on'},
        )
        self.assertRedirects(respuesta, reverse('estudiantes:estudiante_detalle', args=[self.estudiante.pk]))
        self.assertEqual(self.estudiante.representante_legal, self.madre)

    def test_cedula_no_registrada_muestra_error(self):
        respuesta = self.client.post(
            reverse('estudiantes:relacion_crear', args=[self.estudiante.pk]),
            {'cedula_representante': '99999999', 'parentesco': 'PADRE'},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('cedula_representante', respuesta.context['form'].errors)

    def test_representante_ya_asignado_muestra_error(self):
        EstudianteRepresentante.objects.create(
            estudiante=self.estudiante, representante=self.madre, parentesco='MADRE'
        )
        respuesta = self.client.post(
            reverse('estudiantes:relacion_crear', args=[self.estudiante.pk]),
            {'cedula_representante': '12345678', 'parentesco': 'OTRO'},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('cedula_representante', respuesta.context['form'].errors)
        self.assertEqual(self.estudiante.relaciones_representante.count(), 1)

    def test_segundo_representante_legal_es_rechazado(self):
        EstudianteRepresentante.objects.create(
            estudiante=self.estudiante, representante=self.madre,
            parentesco='MADRE', es_representante_legal=True,
        )
        crear_representante('87654321', nombres='Pedro')
        respuesta = self.client.post(
            reverse('estudiantes:relacion_crear', args=[self.estudiante.pk]),
            {'cedula_representante': '87654321', 'parentesco': 'PADRE', 'es_representante_legal': 'on'},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'ya tiene un representante legal')

    def test_quitar_vinculo_conserva_al_representante(self):
        relacion = EstudianteRepresentante.objects.create(
            estudiante=self.estudiante, representante=self.madre, parentesco='MADRE'
        )
        respuesta = self.client.post(reverse('estudiantes:relacion_quitar', args=[relacion.pk]))
        self.assertRedirects(respuesta, reverse('estudiantes:estudiante_detalle', args=[self.estudiante.pk]))
        self.assertFalse(EstudianteRepresentante.objects.filter(pk=relacion.pk).exists())
        self.assertTrue(Representante.objects.filter(pk=self.madre.pk).exists())

    def test_administracion_no_puede_asignar_ni_quitar(self):
        relacion = EstudianteRepresentante.objects.create(
            estudiante=self.estudiante, representante=self.madre, parentesco='MADRE'
        )
        self.client.force_login(crear_usuario('cobranzas', ADMINISTRACION))
        self.assertEqual(
            self.client.get(reverse('estudiantes:relacion_crear', args=[self.estudiante.pk])).status_code, 403
        )
        self.assertEqual(
            self.client.post(reverse('estudiantes:relacion_quitar', args=[relacion.pk])).status_code, 403
        )
