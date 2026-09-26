"""
Vistas del módulo de Estudiantes y Representantes.

Permisos (ver usuarios/roles.py):
- Control de Estudios y Director: consultan, registran y modifican.
- Administración: solo consulta (para ubicar al representante al cobrar).
"""
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import (
    AsignarRepresentanteForm,
    EstudianteEditarForm,
    EstudianteForm,
    RelacionRepresentanteForm,
    RepresentanteForm,
)
from .models import Estudiante, EstudianteRepresentante, Representante


# ---------------------------------------------------------------------------
# Estudiantes
# ---------------------------------------------------------------------------
class EstudianteListView(PermissionRequiredMixin, ListView):
    permission_required = 'estudiantes.view_estudiante'
    model = Estudiante
    template_name = 'estudiantes/estudiante_lista.html'
    context_object_name = 'estudiantes'
    paginate_by = 20

    def get_queryset(self):
        # Se trae el representante legal en la misma consulta para mostrarlo en la tabla
        estudiantes = Estudiante.objects.prefetch_related(
            Prefetch(
                'relaciones_representante',
                queryset=EstudianteRepresentante.objects.filter(
                    es_representante_legal=True
                ).select_related('representante'),
                to_attr='relacion_legal',
            )
        )
        busqueda = self.request.GET.get('q', '').strip()
        if busqueda:
            estudiantes = estudiantes.filter(
                Q(cedula_escolar__icontains=busqueda)
                | Q(cedula__icontains=busqueda)
                | Q(nombres__icontains=busqueda)
                | Q(apellidos__icontains=busqueda)
            )
        estatus = self.request.GET.get('estatus', '')
        if estatus in Estudiante.Estatus.values:
            estudiantes = estudiantes.filter(estatus=estatus)
        return estudiantes

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['busqueda'] = self.request.GET.get('q', '')
        contexto['estatus_seleccionado'] = self.request.GET.get('estatus', '')
        contexto['opciones_estatus'] = Estudiante.Estatus.choices
        return contexto


class EstudianteDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'estudiantes.view_estudiante'
    model = Estudiante
    template_name = 'estudiantes/estudiante_detalle.html'
    context_object_name = 'estudiante'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['relaciones'] = self.object.relaciones_representante.select_related(
            'representante'
        ).order_by('-es_representante_legal', 'representante__apellidos')
        return contexto


class EstudianteCreateView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    permission_required = 'estudiantes.add_estudiante'
    model = Estudiante
    form_class = EstudianteForm
    template_name = 'estudiantes/estudiante_form.html'
    success_message = 'Estudiante registrado correctamente. Ahora asigne sus representantes.'

    def get_success_url(self):
        return reverse('estudiantes:estudiante_detalle', args=[self.object.pk])


class EstudianteUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    permission_required = 'estudiantes.change_estudiante'
    model = Estudiante
    form_class = EstudianteEditarForm
    template_name = 'estudiantes/estudiante_form.html'
    success_message = 'Datos del estudiante actualizados correctamente.'

    def get_success_url(self):
        return reverse('estudiantes:estudiante_detalle', args=[self.object.pk])


# ---------------------------------------------------------------------------
# Representantes
# ---------------------------------------------------------------------------
class RepresentanteListView(PermissionRequiredMixin, ListView):
    permission_required = 'estudiantes.view_representante'
    model = Representante
    template_name = 'estudiantes/representante_lista.html'
    context_object_name = 'representantes'
    paginate_by = 20

    def get_queryset(self):
        representantes = Representante.objects.annotate(
            cantidad_estudiantes=Count('relaciones_estudiante')
        )
        busqueda = self.request.GET.get('q', '').strip()
        if busqueda:
            representantes = representantes.filter(
                Q(cedula__icontains=busqueda)
                | Q(nombres__icontains=busqueda)
                | Q(apellidos__icontains=busqueda)
            )
        return representantes

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['busqueda'] = self.request.GET.get('q', '')
        return contexto


class RepresentanteDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'estudiantes.view_representante'
    model = Representante
    template_name = 'estudiantes/representante_detalle.html'
    context_object_name = 'representante'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['relaciones'] = self.object.relaciones_estudiante.select_related(
            'estudiante'
        ).order_by('estudiante__apellidos', 'estudiante__nombres')
        return contexto


class SiguientePaginaMixin:
    """
    Permite volver a la pantalla anterior después de guardar (por ejemplo,
    registrar un representante desde la ficha de un estudiante).
    """
    def get_siguiente(self):
        siguiente = self.request.POST.get('next') or self.request.GET.get('next')
        if siguiente and url_has_allowed_host_and_scheme(
            siguiente, allowed_hosts={self.request.get_host()}
        ):
            return siguiente
        return None

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['next'] = self.get_siguiente() or ''
        return contexto


class RepresentanteCreateView(PermissionRequiredMixin, SuccessMessageMixin, SiguientePaginaMixin, CreateView):
    permission_required = 'estudiantes.add_representante'
    model = Representante
    form_class = RepresentanteForm
    template_name = 'estudiantes/representante_form.html'
    success_message = 'Representante registrado correctamente.'

    def get_success_url(self):
        return self.get_siguiente() or reverse(
            'estudiantes:representante_detalle', args=[self.object.pk]
        )


class RepresentanteUpdateView(PermissionRequiredMixin, SuccessMessageMixin, SiguientePaginaMixin, UpdateView):
    permission_required = 'estudiantes.change_representante'
    model = Representante
    form_class = RepresentanteForm
    template_name = 'estudiantes/representante_form.html'
    success_message = 'Datos del representante actualizados correctamente.'

    def get_success_url(self):
        return self.get_siguiente() or reverse(
            'estudiantes:representante_detalle', args=[self.object.pk]
        )


# ---------------------------------------------------------------------------
# Representantes de un estudiante (tabla intermedia)
# ---------------------------------------------------------------------------
class AsignarRepresentanteView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    permission_required = 'estudiantes.add_estudianterepresentante'
    model = EstudianteRepresentante
    form_class = AsignarRepresentanteForm
    template_name = 'estudiantes/relacion_form.html'
    success_message = 'Representante asignado correctamente.'

    @cached_property
    def estudiante(self):
        return get_object_or_404(Estudiante, pk=self.kwargs['estudiante_pk'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['estudiante'] = self.estudiante
        return kwargs

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['estudiante'] = self.estudiante
        return contexto

    def get_success_url(self):
        return reverse('estudiantes:estudiante_detalle', args=[self.estudiante.pk])


class RelacionUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    permission_required = 'estudiantes.change_estudianterepresentante'
    model = EstudianteRepresentante
    form_class = RelacionRepresentanteForm
    template_name = 'estudiantes/relacion_form.html'
    context_object_name = 'relacion'
    success_message = 'Datos del representante actualizados correctamente.'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['estudiante'] = self.object.estudiante
        return contexto

    def get_success_url(self):
        return reverse('estudiantes:estudiante_detalle', args=[self.object.estudiante_id])


class RelacionDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    """Quita el vínculo con un representante; no borra los datos del representante."""
    permission_required = 'estudiantes.delete_estudianterepresentante'
    model = EstudianteRepresentante
    template_name = 'estudiantes/relacion_confirmar_quitar.html'
    context_object_name = 'relacion'
    success_message = 'Representante desvinculado del estudiante.'

    def get_success_url(self):
        return reverse('estudiantes:estudiante_detalle', args=[self.object.estudiante_id])
