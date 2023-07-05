import os
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import logout, login, authenticate
from django.contrib import messages
from .models import *
import playsound
from .forms import *
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.core.mail import EmailMessage
import sys
from django.contrib.auth.views import PasswordResetView
import cv2
from pyzbar import pyzbar
from datetime import datetime
import qrcode
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.conf import settings
from django.core.mail import send_mail
import random
import string
from django.template.loader import render_to_string
from django.contrib.auth.hashers import make_password

sys.path.append('..')
from app.detection import FaceRecognition

faceRecognition = FaceRecognition()


def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string


def home(request):
    trainers = Trainer.objects.annotate(total_students=Sum('classroom__max_capacity'))
    classrooms = Classroom.objects.all()

    attendee_classrooms = None
    if request.user.is_authenticated and hasattr(request.user, 'attendee'):
        attendee_classrooms = request.user.attendee.classrooms.all()

    if request.user.is_authenticated and hasattr(request.user, 'trainer'):
        classrooms = request.user.trainer.classroom_set.all()

    context = {'trainers': trainers, 'classrooms': classrooms, 'attendee_classrooms': attendee_classrooms}
    return render(request, 'app/home.html', context)


def loginPage(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username_email = request.POST['username_email']
        password = request.POST['password']
        user = None

        # Check if the input is an email
        if '@' in username_email:
            try:
                user = User.objects.get(email=username_email)
            except User.DoesNotExist:
                messages.error(request, 'User does not exist!')
                return redirect('home')
        # If not an email, check if it is a username
        if user is None:
            try:
                user = User.objects.get(username=username_email)
            except User.DoesNotExist:
                messages.error(request, 'User does not exist!')
                return redirect('home')
        # Authenticate the user if found
        if user is not None:
            user = authenticate(username=user.username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Invalid password!')
        else:
            messages.error(request, 'User does not exist!')
    classrooms = Classroom.objects.all()
    trainers = Trainer.objects.all()
    context = {
        'classrooms': classrooms,
        'trainers': trainers,
    }
    return render(request, 'app/home.html', context)


def logoutUser(request):
    logout(request)
    return redirect('home')


def addFace(face_id):
    face_id = face_id
    faceRecognition.faceDetect(face_id)
    return redirect('/')


@login_required(login_url='login')
def ListAttendee(request):
    if not request.user.is_staff and not request.user.is_superuser:
        # if user is not admin
        return HttpResponse(status=404)
    attendees = Attendee.objects.all()
    context = {'attendees': attendees}
    return render(request, 'app/list_attendee.html', context)