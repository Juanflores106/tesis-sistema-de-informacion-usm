"""
Formularios del módulo de Estudiantes y Representantes.
Se muestran con Bootstrap 5 mediante django-crispy-forms.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Estudiante, EstudianteRepresentante, Representante, validar_cedula


class FechaInput(forms.DateInput):
    """Campo de fecha con calendario del navegador."""
    input_type = 'date'

    def __init__(self, **kwargs):
        super().__init__(format='%Y-%m-%d', **kwargs)


def validar_fecha_pasada(fecha):
    if fecha and fecha > timezone.localdate():
        raise ValidationError('La fecha de nacimiento no puede ser posterior a hoy.')
    return fecha


# ---------------------------------------------------------------------------
# Representante
# ---------------------------------------------------------------------------
class RepresentanteForm(forms.ModelForm):
    class Meta:
        model = Representante
        fields = [
            'nacionalidad', 'cedula', 'nombres', 'apellidos', 'sexo',
            'fecha_nacimiento', 'telefono_principal', 'telefono_secundario',
            'correo', 'ocupacion', 'lugar_trabajo', 'direccion',
        ]
        widgets = {
            'fecha_nacimiento': FechaInput(),
            'direccion': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'fecha_nacimiento': 'Fecha de nacimiento',
            'telefono_principal': 'Teléfono principal',
            'telefono_secundario': 'Teléfono secundario',
        }
        help_texts = {
            'cedula': 'Solo números, sin puntos. Ejemplo: 12345678',
            'telefono_principal': 'Ejemplo: 0414-1234567',
        }

    def clean_fecha_nacimiento(self):
        return validar_fecha_pasada(self.cleaned_data.get('fecha_nacimiento'))


# ---------------------------------------------------------------------------
# Estudiante
# ---------------------------------------------------------------------------
class EstudianteForm(forms.ModelForm):
    """Registro de un estudiante nuevo: siempre ingresa con estatus Activo."""
    class Meta:
        model = Estudiante
        fields = [
            'nacionalidad', 'cedula_escolar', 'cedula', 'nombres', 'apellidos',
            'sexo', 'fecha_nacimiento', 'lugar_nacimiento', 'direccion',
            'condiciones_medicas',
        ]
        widgets = {
            'fecha_nacimiento': FechaInput(),
            'direccion': forms.Textarea(attrs={'rows': 2}),
            'condiciones_medicas': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'fecha_nacimiento': 'Fecha de nacimiento',
            'lugar_nacimiento': 'Lugar de nacimiento',
        }

    def clean_fecha_nacimiento(self):
        return validar_fecha_pasada(self.cleaned_data.get('fecha_nacimiento'))


class EstudianteEditarForm(EstudianteForm):
    """Modificación de los datos del estudiante, incluido su estatus (retiro o egreso)."""
    class Meta(EstudianteForm.Meta):
        fields = EstudianteForm.Meta.fields + ['estatus']


# ---------------------------------------------------------------------------
# Relación estudiante - representante
# ---------------------------------------------------------------------------
class AsignarRepresentanteForm(forms.ModelForm):
    """
    Vincula un representante YA REGISTRADO a un estudiante, buscándolo por
    su cédula (más rápido para la secretaría que buscarlo en una lista).
    """
    cedula_representante = forms.CharField(
        label='Cédula del representante',
        max_length=9,
        validators=[validar_cedula],
        help_text='El representante debe estar registrado previamente.',
    )

    field_order = ['cedula_representante', 'parentesco', 'es_representante_legal', 'autorizado_retirar']

    class Meta:
        model = EstudianteRepresentante
        fields = ['parentesco', 'es_representante_legal', 'autorizado_retirar']

    def __init__(self, *args, estudiante, **kwargs):
        super().__init__(*args, **kwargs)
        # El estudiante se asigna antes de validar para que clean() del modelo
        # pueda verificar la regla del representante legal único.
        self.instance.estudiante = estudiante

    def clean_cedula_representante(self):
        cedula = self.cleaned_data['cedula_representante']
        representante = Representante.objects.filter(cedula=cedula).first()
        if representante is None:
            raise ValidationError(
                'No existe un representante registrado con esa cédula. Regístrelo primero.'
            )
        if EstudianteRepresentante.objects.filter(
            estudiante=self.instance.estudiante, representante=representante
        ).exists():
            raise ValidationError('Este representante ya está asignado al estudiante.')
        self.instance.representante = representante
        return cedula


class RelacionRepresentanteForm(forms.ModelForm):
    """Modifica el parentesco o las autorizaciones de un representante ya asignado."""
    class Meta:
        model = EstudianteRepresentante
        fields = ['parentesco', 'es_representante_legal', 'autorizado_retirar']
