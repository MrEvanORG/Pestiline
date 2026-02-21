from django.apps import AppConfig


class ResumeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'resume'
    verbose_name = 'برنامه رزومه'

    def ready(self):
        import resume.signals


