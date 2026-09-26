"""
Registro de los modelos del módulo de Estudiantes en el panel de administración.
Permite probar el registro de estudiantes y representantes desde /admin
mientras se construyen las interfaces definitivas con Bootstrap.
"""
from django.contrib import admin

from .models import Estudiante, EstudianteRepresentante, Representante


class RelacionRepresentanteInline(admin.TabularInline):
    """Permite asignar representantes desde la misma ficha del estudiante."""
    model = EstudianteRepresentante
    extra = 1
    autocomplete_fields = ['representante']


@admin.register(Representante)
class RepresentanteAdmin(admin.ModelAdmin):
    list_display = ('cedula', 'nombres', 'apellidos', 'telefono_principal', 'correo')
    search_fields = ('cedula', 'nombres', 'apellidos')


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ('cedula_escolar', 'nombres', 'apellidos', 'fecha_nacimiento', 'estatus')
    list_filter = ('estatus', 'sexo')
    search_fields = ('cedula_escolar', 'cedula', 'nombres', 'apellidos')
    inlines = [RelacionRepresentanteInline]
