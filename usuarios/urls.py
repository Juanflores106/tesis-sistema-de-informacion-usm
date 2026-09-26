from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = 'usuarios'

urlpatterns = [
    path('iniciar-sesion/', views.IniciarSesionView.as_view(), name='login'),
    path('cerrar-sesion/', LogoutView.as_view(), name='logout'),
    path('cambiar-clave/', views.CambiarClaveView.as_view(), name='cambiar_clave'),
    path('', views.UsuarioListView.as_view(), name='lista'),
    path('nuevo/', views.UsuarioCreateView.as_view(), name='crear'),
    path('<int:pk>/editar/', views.UsuarioUpdateView.as_view(), name='editar'),
    path('<int:pk>/clave/', views.EstablecerClaveView.as_view(), name='establecer_clave'),
    path('<int:pk>/estado/', views.CambiarEstadoUsuarioView.as_view(), name='cambiar_estado'),
]
