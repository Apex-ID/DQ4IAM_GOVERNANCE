from django.apps import AppConfig


class MelhoriaContinuaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'melhoria_continua'

    def ready(self):
        import melhoria_continua.signals
