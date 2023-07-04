from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Attendee)
admin.site.register(Trainer)


class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'building', 'floor', 'max_capacity', 'TrainerName')

    def TrainerName(self, obj):
        return obj.trainer.name


admin.site.register(Classroom, ClassroomAdmin)
admin.site.register(Attendance)
admin.site.register(ClassroomResource)
