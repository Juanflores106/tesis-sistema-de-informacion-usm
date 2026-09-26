"""
Rutas (URL) principales del sistema.
Cada módulo define sus propias rutas en su archivo urls.py y aquí se incluyen.
"""
from django.contrib import admin
from django.urls import include, path

from usuarios.views import InicioView

admin.site.site_header = 'Colegio Marycarmen - Administración'
admin.site.site_title = 'Colegio Marycarmen'
admin.site.index_title = 'Panel de administración'

urlpatterns = [
    path('', InicioView.as_view(), name='inicio'),
    path('usuarios/', include('usuarios.urls')),
    path('estudiantes/', include('estudiantes.urls')),
    path('admin/', admin.site.urls),
]
