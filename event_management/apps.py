from django.apps import AppConfig

class EventManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'event_management'
    
    def ready(self):
        import event_management.signals  # Import signals when app is ready
