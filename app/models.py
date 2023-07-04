from django.db import models
from django.contrib.auth.models import User


class Attendee(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    profile_pic = models.ImageField(default='avatar.svg', null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateField(auto_now=True)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True)
    classrooms = models.ManyToManyField('Classroom', related_name='attendees')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Attendee"
        verbose_name_plural = "Attendees"
        db_table = 'Attendee'


class Trainer(models.Model):
    name = models.CharField(max_length=100)
    expertise = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    profile_pic = models.ImageField(default='avatar.svg', null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateField(auto_now=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Trainer"
        verbose_name_plural = "Trainers"
        db_table = 'Trainer'


class Classroom(models.Model):
    name = models.CharField(max_length=100)
    building = models.CharField(max_length=100)
    floor = models.IntegerField()
    max_capacity = models.IntegerField()
    description = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateField(auto_now=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    code = models.CharField(max_length=8, null=True)
    profile_pic = models.ImageField(default='avatar.svg', null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Classroom"
        verbose_name_plural = "Classrooms"
        db_table = 'Classroom'


class Attendance(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    attendee = models.ForeignKey(Attendee, on_delete=models.CASCADE)
    is_present = models.BooleanField()
    check_in_time = models.DateTimeField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateField(auto_now=True)

    def __str__(self):
        return self.attendee.name

    class Meta:
        verbose_name = "Attendance"
        verbose_name_plural = "Attendance"
        db_table = 'Attendance'


class ClassroomResource(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to='classroom_files/')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Classroom Resource"
        verbose_name_plural = "Classroom Resources"
        db_table = 'ClassroomResource'
        ordering = ['-created', '-updated']


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=500)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.sender.username

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        db_table = 'Messages'

