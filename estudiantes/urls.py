from django.urls import path

from . import views

app_name = 'estudiantes'

urlpatterns = [
    # Estudiantes
    path('', views.EstudianteListView.as_view(), name='estudiante_lista'),
    path('nuevo/', views.EstudianteCreateView.as_view(), name='estudiante_crear'),
    path('<int:pk>/', views.EstudianteDetailView.as_view(), name='estudiante_detalle'),
    path('<int:pk>/editar/', views.EstudianteUpdateView.as_view(), name='estudiante_editar'),
    # Representantes de un estudiante
    path(
        '<int:estudiante_pk>/representantes/asignar/',
        views.AsignarRepresentanteView.as_view(),
        name='relacion_crear',
    ),
    path('relaciones/<int:pk>/editar/', views.RelacionUpdateView.as_view(), name='relacion_editar'),
    path('relaciones/<int:pk>/quitar/', views.RelacionDeleteView.as_view(), name='relacion_quitar'),
    # Representantes
    path('representantes/', views.RepresentanteListView.as_view(), name='representante_lista'),
    path('representantes/nuevo/', views.RepresentanteCreateView.as_view(), name='representante_crear'),
    path('representantes/<int:pk>/', views.RepresentanteDetailView.as_view(), name='representante_detalle'),
    path(
        'representantes/<int:pk>/editar/',
        views.RepresentanteUpdateView.as_view(),
        name='representante_editar',
    ),
]
