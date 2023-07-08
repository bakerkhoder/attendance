from django.apps import AppConfig
from django.utils import timezone

class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        # if you face problem like app
        # are not ready yet move the import inside the function
        from .models import Attendance
        twenty_four_hours_ago = timezone.now() - timezone.timedelta(hours=24)
        Attendance.objects.filter(created__lt=twenty_four_hours_ago).update(is_present = False, check_in_time = None)