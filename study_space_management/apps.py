# study_space_management/apps.py

from django.apps import AppConfig

class StudySpaceManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'study_space_management'

    def ready(self):
        import study_space_management.signals