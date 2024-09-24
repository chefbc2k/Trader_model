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
BASE_DIR = Path(__file__).resolve().parent.parent  # This should point to 'Hybrid_Trading/'
print("BASE_DIR:", BASE_DIR)

# Security
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')  # Loaded directly from the environment
DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() in ('true', '1', 't', 'yes')

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
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Allows serving static files in development
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

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
    os.path.join(BASE_DIR, 'Hybrid_Trading', 'Web_interface', 'static'),
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
    'handlers': {
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'Hybrid_Trading_logs.log'),
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'hybrid_trading': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

# Channels (WebSocket configuration)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],  # Redis configuration
        },
    },
}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'