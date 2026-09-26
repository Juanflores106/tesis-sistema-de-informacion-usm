"""
Configuración del proyecto Django.
Sistema de Información para la Gestión Académica y Financiera - Colegio Marycarmen.

Los datos sensibles (clave secreta y clave de la base de datos) se leen de
variables de entorno. Los valores por defecto sirven SOLO para desarrollo;
en el servidor del colegio deben definirse las variables (ver README.md).
"""
import os
from pathlib import Path

from django.contrib.messages import constants as mensajes

# Carpeta raíz del proyecto (donde está manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Seguridad
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-solo-para-desarrollo-cambiar-en-el-servidor-del-colegio',
)
DEBUG = os.environ.get('DJANGO_DEBUG', '1') == '1'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


# ---------------------------------------------------------------------------
# Aplicaciones
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Librerías
    'crispy_forms',
    'crispy_bootstrap5',
    # Módulos del sistema
    'usuarios',
    'estudiantes',
    'academico',
    'inscripciones',
    'finanzas',
    'reportes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'usuarios.context_processors.rol_usuario',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ---------------------------------------------------------------------------
# Base de datos: MySQL 8.4 LTS
# (No usar XAMPP: su MariaDB 10.4 no es compatible con Django 5.1 o superior.)
#
# Para una prueba rápida sin MySQL se puede definir DB_ENGINE=sqlite; el
# sistema usará entonces un archivo db.sqlite3 local.
# ---------------------------------------------------------------------------
if os.environ.get('DB_ENGINE') == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('DB_NAME', 'colegio_marycarmen'),
            'USER': os.environ.get('DB_USER', 'marycarmen_app'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'CambiaEstaClave2026'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '3306'),
            'OPTIONS': {'charset': 'utf8mb4'},
            # La base de datos temporal de las pruebas usa la misma codificación
            'TEST': {'CHARSET': 'utf8mb4', 'COLLATION': 'utf8mb4_unicode_ci'},
        }
    }


# ---------------------------------------------------------------------------
# Contraseñas
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ---------------------------------------------------------------------------
# Idioma y zona horaria
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'es-ve'
TIME_ZONE = 'America/Caracas'
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Archivos estáticos (CSS, JavaScript, imágenes)
# Bootstrap se guarda dentro del proyecto (static/vendor) para que el sistema
# funcione aunque el colegio no tenga conexión a Internet.
# ---------------------------------------------------------------------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---------------------------------------------------------------------------
# Formularios con Bootstrap 5 (django-crispy-forms)
# ---------------------------------------------------------------------------
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'


# ---------------------------------------------------------------------------
# Inicio y cierre de sesión
# ---------------------------------------------------------------------------
LOGIN_URL = 'usuarios:login'
LOGIN_REDIRECT_URL = 'inicio'
LOGOUT_REDIRECT_URL = 'usuarios:login'

# La sesión se cierra al cerrar el navegador (equipos compartidos en la oficina)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Los mensajes de error de Django usan la clase "danger" de Bootstrap
MESSAGE_TAGS = {mensajes.ERROR: 'danger'}
