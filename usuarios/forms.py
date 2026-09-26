"""
Formularios del módulo de Usuarios y seguridad.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import transaction

from estudiantes.models import validar_cedula, validar_telefono

from .models import Perfil
from .roles import ROLES


ETIQUETAS_USUARIO = {
    'first_name': 'Nombres',
    'last_name': 'Apellidos',
    'email': 'Correo electrónico',
}


class DatosTrabajadorForm(forms.Form):
    """Campos comunes al registrar y al modificar un usuario: rol y datos del perfil."""
    rol = forms.ModelChoiceField(
        queryset=Group.objects.filter(name__in=ROLES).order_by('name'),
        label='Rol',
        empty_label='Seleccione...',
    )
    cedula = forms.CharField(
        label='Cédula de identidad', max_length=9, validators=[validar_cedula]
    )
    cargo = forms.CharField(max_length=80)
    telefono = forms.CharField(
        label='Teléfono',
        max_length=12,
        required=False,
        validators=[validar_telefono],
        help_text='Ejemplo: 0414-1234567',
    )

    def __init__(self, *args, usuario_actual=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        # Un usuario no puede cambiar su propio rol (evita quedarse sin acceso).
        if usuario_actual is not None and usuario_actual == self.instance:
            self.fields['rol'].disabled = True
            self.fields['rol'].required = False
            self.fields['rol'].help_text = 'No puede cambiar su propio rol.'

    def clean_cedula(self):
        cedula = self.cleaned_data['cedula']
        otros = Perfil.objects.filter(cedula=cedula)
        if self.instance.pk:
            otros = otros.exclude(usuario=self.instance)
        if otros.exists():
            raise ValidationError('Ya existe un usuario registrado con esta cédula.')
        return cedula

    def guardar_perfil_y_rol(self, usuario):
        if not self.fields['rol'].disabled:
            usuario.groups.set([self.cleaned_data['rol']])
        Perfil.objects.update_or_create(
            usuario=usuario,
            defaults={
                'cedula': self.cleaned_data['cedula'],
                'cargo': self.cleaned_data['cargo'],
                'telefono': self.cleaned_data['telefono'],
            },
        )


class UsuarioCrearForm(DatosTrabajadorForm, UserCreationForm):
    field_order = [
        'first_name', 'last_name', 'cedula', 'cargo', 'telefono', 'email',
        'rol', 'username', 'password1', 'password2',
    ]

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        labels = ETIQUETAS_USUARIO

    @transaction.atomic
    def save(self, commit=True):
        usuario = super().save(commit=True)
        self.guardar_perfil_y_rol(usuario)
        return usuario


class UsuarioEditarForm(DatosTrabajadorForm, forms.ModelForm):
    field_order = [
        'first_name', 'last_name', 'cedula', 'cargo', 'telefono', 'email',
        'rol', 'username',
    ]

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        labels = ETIQUETAS_USUARIO

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        perfil = getattr(self.instance, 'perfil', None)
        if perfil:
            self.initial.update(
                cedula=perfil.cedula, cargo=perfil.cargo, telefono=perfil.telefono
            )
        rol = self.instance.groups.filter(name__in=ROLES).first()
        self.initial['rol'] = rol.pk if rol else None

    @transaction.atomic
    def save(self, commit=True):
        usuario = super().save(commit=True)
        self.guardar_perfil_y_rol(usuario)
        return usuario
