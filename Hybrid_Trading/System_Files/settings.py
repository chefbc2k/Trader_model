"""
Django settings for Hybrid_Trading project.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from Hybrid_Trading.Log.Logging_Master import LoggingMaster  # Only import if you're using it

# Load environment variables from the .env file
load_dotenv()

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent  # Directly points to Hybrid_Trading

# Security settings
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')  # Load secret key from environment variable
DEBUG = os.getenv('DJANGO_DEBUG', 'TRUE').lower() in ('true', '1', 't', 'yes')
ALLOWED_HOSTS = ['localhost', '127.0.0.1']  # Add more hosts if needed

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap4',
    'debug_toolbar',
    'channels',  # For WebSocket support

    # Hybrid Trading apps
    'Hybrid_Trading',  # Main app
    'Hybrid_Trading.Daytrader',
    'Hybrid_Trading.Web_interface',
    'Hybrid_Trading.Symbols',
    'Hybrid_Trading.Modes',
    'Hybrid_Trading.Model_Trainer',
    'Hybrid_Trading.Forecaster',
    'Hybrid_Trading.Data',
    'Hybrid_Trading.Backtester',
    'Hybrid_Trading.Analysis',
    'Hybrid_Trading.Trading',
    'Hybrid_Trading.Dashboard',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serves static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Debug Toolbar settings
INTERNAL_IPS = [
    '127.0.0.1',
    # Add more IPs for debugging if necessary
]

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
]

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
    'SHOW_TEMPLATE_CONTEXT': True,
}

# URL configuration
ROOT_URLCONF = 'Hybrid_Trading.System_Files.urls'

# Template settings
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'Hybrid_Trading', 'Trading', 'templates'),
            os.path.join(BASE_DIR, 'Hybrid_Trading', 'Dashboard', 'templates'),
            os.path.join(BASE_DIR, 'Hybrid_Trading', 'Strategy', 'templates'),
            os.path.join(BASE_DIR, 'Hybrid_Trading', 'Model_Trainer', 'templates'),
            os.path.join(BASE_DIR, 'Hybrid_Trading', 'Forecaster', 'templates'),
            os.path.join(BASE_DIR, 'Hybrid_Trading', 'Backtester', 'templates'),
            os.path.join(BASE_DIR, 'Hybrid_Trading', 'Web_interface', 'templates'),
            os.path.join(BASE_DIR, 'Hybrid_Trading', 'Analysis', 'templates'),
        ],
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

# WSGI and ASGI application configuration
WSGI_APPLICATION = 'Hybrid_Trading.System_Files.wsgi.application'
ASGI_APPLICATION = 'Hybrid_Trading.System_Files.asgi.application'

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'options': '-c search_path="Hybrid_Trading_Schema"'
        },
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    # Add other validators as necessary
]

# Localization settings
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'  # Adjust as per your time zone
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR.parent, 'Web_interface', 'static'),
]

# Static root for production
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Logging configuration using LoggingMaster
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'Hybrid_Trading_logs.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'hybrid_trading': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Channels configuration for WebSockets
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms configuration
CRISPY_TEMPLATE_PACK = 'bootstrap4'  # Bootstrap 4 form template pack