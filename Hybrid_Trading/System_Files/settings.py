"""
Django settings for Hybrid_Trading project.
"""
import os
from Hybrid_Trading.Log.Logging_Master import LoggingMaster  # You still import this if you're using it in your project
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent  # This now points directly to Hybrid_Trading 


# Security
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')  # Loaded directly from the environment
DEBUG = os.getenv('DJANGO_DEBUG', 'TRUE').lower() in ('true', '1', 't', 'yes')

ALLOWED_HOSTS = ['localhost', '127.0.0.1']  # Add your allowed hosts here if necessary

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'Hybrid_Trading',  # Main app
     'debug_toolbar',
    'channels',  # Channels for WebSockets
    'Hybrid_Trading.Web_interface',
    'Hybrid_Trading.Symbols',
    'Hybrid_Trading.Modes',
    'Hybrid_Trading.Model_Trainer',
    'Hybrid_Trading.Forecaster',
    'Hybrid_Trading.Data',
    'Hybrid_Trading.Backtester',
    'Hybrid_Trading.Analysis',
    'Hybrid_Trading.Inputs',
    'Hybrid_Trading.Trading',
    'Hybrid_Trading.Dashboard',
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware', 
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Allows serving static files in development
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
    # Add any other IPs you want to allow, e.g., '192.168.1.100',
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
# Update ROOT_URLCONF
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
            os.path.join(BASE_DIR, 'Hybrid_Trading', 'Inputs', 'templates'),
        ],
        'APP_DIRS': True,  # This allows Django to find templates in app-specific directories
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

# WSGI and ASGI configuration
WSGI_APPLICATION = 'Hybrid_Trading.System_Files.wsgi.application'
ASGI_APPLICATION = 'Hybrid_Trading.System_Files.asgi.application'

# Database Configuration
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

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'  # Adjust to your timezone if necessary
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

# Where Django looks for static files during development
STATICFILES_DIRS = [
os.path.join(BASE_DIR.parent, 'Web_interface', 'static'), 
]

# For production (where static files are collected)
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
            'level': 'DEBUG',  # Show everything from debug level upwards in the console
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'DEBUG',  # Capture everything from debug level upwards in the log file
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'Hybrid_Trading_logs.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',  # Show all Django-related logs at DEBUG level
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['file'],
            'level': 'DEBUG',  # Capture all database-related logs
            'propagate': False,
        },
        'hybrid_trading': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',  # Set 'hybrid_trading' app logging level to DEBUG
            'propagate': True,
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'ERROR',  # Log errors only for HTTP requests
            'propagate': False,
        },
        'django.security': {
            'handlers': ['file'],
            'level': 'WARNING',  # Capture security warnings in the log file
            'propagate': False,
        },
    },
}

# Channels (WebSocket configuration)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'