"""
Vistas del módulo de Usuarios y seguridad: inicio de sesión, pantalla de
inicio y administración de usuarios (solo el Director).

El acceso se controla con los permisos de cada rol (ver roles.py):
PermissionRequiredMixin envía al inicio de sesión a quien no ha entrado y
muestra "acceso denegado" (error 403) a quien no tiene el permiso.
"""
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, FormView, ListView, TemplateView, UpdateView
from django.views.generic.detail import SingleObjectMixin

from estudiantes.models import Estudiante, Representante

from .forms import UsuarioCrearForm, UsuarioEditarForm


# ---------------------------------------------------------------------------
# Sesión
# ---------------------------------------------------------------------------
class IniciarSesionView(LoginView):
    template_name = 'usuarios/login.html'
    redirect_authenticated_user = True


class CambiarClaveView(SuccessMessageMixin, PasswordChangeView):
    """Cualquier usuario puede cambiar su propia contraseña."""
    template_name = 'usuarios/cambiar_clave.html'
    success_url = reverse_lazy('inicio')
    success_message = 'Su contraseña fue actualizada correctamente.'


class InicioView(LoginRequiredMixin, TemplateView):
    """Pantalla principal: muestra un resumen según los permisos del rol."""
    template_name = 'inicio.html'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        usuario = self.request.user
        if usuario.has_perm('estudiantes.view_estudiante'):
            contexto['total_estudiantes_activos'] = Estudiante.objects.filter(
                estatus=Estudiante.Estatus.ACTIVO
            ).count()
        if usuario.has_perm('estudiantes.view_representante'):
            contexto['total_representantes'] = Representante.objects.count()
        if usuario.has_perm('auth.view_user'):
            contexto['total_usuarios_activos'] = User.objects.filter(
                is_active=True, is_superuser=False
            ).count()
        return contexto


# ---------------------------------------------------------------------------
# Administración de usuarios (rol Director)
# ---------------------------------------------------------------------------
class UsuarioQuerysetMixin:
    """
    Las cuentas de administrador técnico (superusuario, creado con
    createsuperuser) solo las puede ver otro superusuario.
    """
    def get_queryset(self):
        usuarios = User.objects.select_related('perfil').prefetch_related('groups')
        if not self.request.user.is_superuser:
            usuarios = usuarios.filter(is_superuser=False)
        return usuarios


class UsuarioListView(PermissionRequiredMixin, UsuarioQuerysetMixin, ListView):
    permission_required = 'auth.view_user'
    template_name = 'usuarios/usuario_lista.html'
    context_object_name = 'usuarios'
    paginate_by = 20

    def get_queryset(self):
        return super().get_queryset().order_by('-is_active', 'last_name', 'first_name')


class UsuarioCreateView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    permission_required = 'auth.add_user'
    form_class = UsuarioCrearForm
    template_name = 'usuarios/usuario_form.html'
    success_url = reverse_lazy('usuarios:lista')
    success_message = 'Usuario "%(username)s" registrado correctamente.'


class UsuarioUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UsuarioQuerysetMixin, UpdateView):
    permission_required = 'auth.change_user'
    form_class = UsuarioEditarForm
    template_name = 'usuarios/usuario_form.html'
    context_object_name = 'usuario'
    success_url = reverse_lazy('usuarios:lista')
    success_message = 'Usuario "%(username)s" actualizado correctamente.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['usuario_actual'] = self.request.user
        return kwargs


class EstablecerClaveView(PermissionRequiredMixin, UsuarioQuerysetMixin, SingleObjectMixin, FormView):
    """El Director asigna una contraseña nueva a un usuario que la olvidó."""
    permission_required = 'auth.change_user'
    form_class = SetPasswordForm
    template_name = 'usuarios/usuario_clave.html'
    context_object_name = 'usuario'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.object
        return kwargs

    def form_valid(self, form):
        form.save()
        if self.object == self.request.user:
            # Evita que se cierre la sesión propia al cambiar la contraseña
            update_session_auth_hash(self.request, self.object)
        messages.success(
            self.request, f'Contraseña de "{self.object.username}" actualizada correctamente.'
        )
        return redirect('usuarios:lista')


class CambiarEstadoUsuarioView(PermissionRequiredMixin, UsuarioQuerysetMixin, SingleObjectMixin, View):
    """
    Activa o desactiva una cuenta. Los usuarios no se eliminan: un usuario
    desactivado no puede iniciar sesión, pero su historial se conserva.
    """
    permission_required = 'auth.change_user'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        usuario = self.get_object()
        if usuario == request.user:
            messages.error(request, 'No puede desactivar su propia cuenta.')
        else:
            usuario.is_active = not usuario.is_active
            usuario.save(update_fields=['is_active'])
            estado = 'activado' if usuario.is_active else 'desactivado'
            messages.success(request, f'Usuario "{usuario.username}" {estado}.')
        return redirect('usuarios:lista')
