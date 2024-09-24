"""
WSGI config for Hybrid_Trading project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import django
from django.core.wsgi import get_wsgi_application

# Set the DJANGO_SETTINGS_MODULE to point to the new path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Hybrid_Trading.System_Files.settings')

# Set up Django
django.setup()

# Define WSGI application
application = get_wsgi_application()