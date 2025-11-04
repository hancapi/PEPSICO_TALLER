#pepsico_taller/pepsico_taller/settings.py

import pymysql 
pymysql.install_as_MySQLdb()
from decouple import config, Csv
import os
from pathlib import Path
"""
Django settings for pepsico_taller project.
Configuración para PepsiCo Taller - Gestión de Flota Vehicular
"""

AUTH_USER_MODEL = 'autenticacion.Empleado'
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.loca.lt']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'autenticacion',
    'vehiculos',
    'talleres',
    'reportes',
    'documentos',
    'ordenestrabajo',
    'rest_framework',
    'utils',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pepsico_taller.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}



STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']


# Carpeta donde se almacenarán los archivos subidos
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000", 
    "http://localhost:8000",
    "https://testeorepocaps.loca.lt",
]
CORS_ALLOW_ALL_ORIGINS = True  # Temporalmente para desarrollo
CORS_ALLOW_CREDENTIALS = True

LOGIN_URL = 'inicio-sesion'
LOGIN_REDIRECT_URL = 'inicio'
LOGOUT_REDIRECT_URL = 'inicio-sesion'

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

#se configurarar mas tarde el envio de correos
#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#EMAIL_HOST = config('EMAIL_HOST')
#EMAIL_PORT = config('EMAIL_PORT', cast=int)
#EMAIL_HOST_USER = config('EMAIL_HOST_USER')
#EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
#EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
