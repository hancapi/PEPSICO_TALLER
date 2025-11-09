# pepsico_taller/settings.py
import pymysql
pymysql.install_as_MySQLdb()

from decouple import config
import os
from pathlib import Path

# ======================
# 🔹 CONFIGURACIÓN BASE
# ======================
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.loca.lt', '*']  # en dev

# ======================
# 🔹 APLICACIONES
# ======================
INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 3rd party
    'corsheaders',
    'rest_framework',

    # Apps del proyecto
    'autenticacion',
    'vehiculos',
    'talleres',
    'reportes',
    'documentos',
    'ordenestrabajo',
    'utils',
]

# ======================
# 🔹 MIDDLEWARE
# ======================
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

# ======================
# 🔹 URLS / TEMPLATES
# ======================
ROOT_URLCONF = 'pepsico_taller.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # usa /templates del proyecto
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

WSGI_APPLICATION = 'pepsico_taller.wsgi.application'

# ======================
# 🔹 BASE DE DATOS (MySQL)
# ======================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# ======================
# 🔹 AUTENTICACIÓN
# ======================
# NO usamos AUTH_USER_MODEL custom. Autenticamos contra 'empleados' con un backend.
AUTHENTICATION_BACKENDS = [
    'autenticacion.backends.EmpleadosBackend',
    'django.contrib.auth.backends.ModelBackend',  # fallback
]

LOGIN_URL = 'inicio-sesion'
LOGIN_REDIRECT_URL = 'inicio'
LOGOUT_REDIRECT_URL = 'inicio-sesion'

# ======================
# 🔹 ARCHIVOS ESTÁTICOS / MEDIA
# ======================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'  

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ======================
# 🔹 CORS (Frontend)
# ======================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "https://testeorepocaps.loca.lt",
]
CORS_ALLOW_ALL_ORIGINS = True  # Solo en desarrollo
CORS_ALLOW_CREDENTIALS = True

# ======================
# 🔹 LOCALIZACIÓN
# ======================
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ======================
# 🔹 EMAIL (dev a consola)
# ======================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
