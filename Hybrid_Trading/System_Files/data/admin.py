from django.apps import apps
from django.contrib import admin
from django.db.models import CharField

# Dynamically get all models from the 'system_files_data' app
app_models = apps.get_app_config('system_files_data').get_models()  # Updated app label

# Register all models dynamically
for model in app_models:
    # Dynamically create an admin class for each model
    class Admin(admin.ModelAdmin):
        list_display = [field.name for field in model._meta.fields]  # Display all fields
        search_fields = [field.name for field in model._meta.fields if isinstance(field, CharField)]  # Searchable fields (only CharFields)
        list_filter = [field.name for field in model._meta.fields]  # Filterable fields

    # Register the model and the dynamically created admin class
    admin.site.register(model, Admin)