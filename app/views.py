from app.detection import FaceRecognition
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

faceRecognition = FaceRecognition()


def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string


def home(request):
    trainers = Trainer.objects.annotate(
        total_students=Sum('classroom__max_capacity'))
    classrooms = Classroom.objects.all()

    attendee_classrooms = None
    if request.user.is_authenticated and hasattr(request.user, 'attendee'):
        attendee_classrooms = request.user.attendee.classrooms.all()

    if request.user.is_authenticated and hasattr(request.user, 'trainer'):
        classrooms = request.user.trainer.classroom_set.all()

    context = {'trainers': trainers, 'classrooms': classrooms,
               'attendee_classrooms': attendee_classrooms}
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


@login_required(login_url='login')
def AddAttendeePage(request):
    if not request.user.is_staff and not request.user.is_superuser:
        # if user is not admin
        return HttpResponse(status=404)
    user_form = UserRegistrationForm()
    attendee_form = AttendeeForm()
    return render(request, 'app/add_attendee.html', {'user_form': user_form,
                                                     'attendee_form': attendee_form})


@login_required(login_url='login')
def AddAttendee(request):
    if not request.user.is_staff and not request.user.is_superuser:
        # if user is not admin
        return HttpResponse(status=404)
    user_form = UserRegistrationForm()
    attendee_form = AttendeeForm()
    users = User.objects.all()
    if request.method == 'POST':
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')

        if pass1 != pass2:
            messages.error(request, 'PASSWORDS ARE NOT EQUAL')
            return redirect('add_attendee')

        user_form = UserRegistrationForm(request.POST)
        attendee_form = AttendeeForm(request.POST, request.FILES)

        if user_form.is_valid() and attendee_form.is_valid():
            user = user_form.save(commit=False)

            for user1 in users:
                if user.email == user1.email:
                    messages.error(request, 'Email already exists!')
                    return redirect('add_attendee')

            email = user.email
            user.save()

            attendee = attendee_form.save(commit=False)
            attendee.email = email
            attendee.user = user
            attendee.save()

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(user.username)
            qr.make(fit=True)
            qr_image = qr.make_image(fill_color="black", back_color="white")
            qr_code_path = f"static/images/{user.username}.png"

            with open(qr_code_path, "wb") as f:
                qr_image.save(f)
            qr_code_img = f"{user.username}.png"

            subject = f'Welcome to OneSchool, {attendee.name}!'
            to_email = attendee.email
            from_email = settings.ADMIN_EMAIL
            email_template = 'app/new_attendee.html'
            user_password = str(request.POST['password1'])
            context_email = {'attendee': attendee, 'password': user_password}
            email_content = render_to_string(email_template, context_email)
            email = EmailMessage(subject, email_content,
                                 from_email, [to_email])
            email.content_subtype = 'html'
            email.attach_file(qr_code_path)
            # email.send()
            # we can send a templte also but we need to change it to pdf using xmlpdf
            # email.send()
            try:
                addFace(user.id)
            except:
                pass
            return redirect('list_attendee')

    context = {
        'user_form': user_form,
        'attendee_form': attendee_form
    }

    return render(request, 'app/add_attendee.html', context)


@login_required(login_url='login')
def UpdateAttendee(request, pk):
    if not request.user.is_staff and not request.user.is_superuser:
        # if user is not admin
        return HttpResponse(status=404)

    attendee = Attendee.objects.get(id=pk)

    if request.method == 'POST':
        attendee_form = AttendeeForm1(
            request.POST, request.FILES, instance=attendee)
        if attendee_form.is_valid():
            email = attendee_form.cleaned_data['email']

            # Check if the email already exists for a user other than the current attendee
            if User.objects.filter(Q(email=email) & ~Q(attendee__id=pk)).exists():
                messages.error(request, 'Email already exists!')
                return redirect('update_attendee', attendee.id)

            attendee_form.save()
            attendee.user.email = email
            attendee.user.save()
            return redirect('list_attendee')
    else:
        attendee_form = AttendeeForm1(instance=attendee)

    context = {
        'attendee_form': attendee_form
    }
    return render(request, 'app/update_attendee.html', context)


@login_required(login_url='login')
def DeleteAttendee(request, pk):
    if not request.user.is_staff and not request.user.is_superuser:
        # if user is not admin
        return HttpResponse(status=404)
    attendee = Attendee.objects.get(id=pk)
    if request.method == 'POST':
        attendee.delete()
        return redirect('list_attendee')
    context = {'attendee': attendee}
    return render(request, 'app/delete_attendee.html', context)


@login_required(login_url='login')
def EditAttendeeProfile(request):
    if not hasattr(request.user, 'attendee'):
        # if user is not student
        return HttpResponse(status=404)

    attendee = Attendee.objects.get(id=request.user.attendee.id)

    if request.method == 'POST':
        attendee_form = AttendeeForm2(
            request.POST, request.FILES, instance=attendee)

        if attendee_form.is_valid():
            email = attendee_form.cleaned_data['email']

            # Check if the email already exists for a user other than the current attendee
            if User.objects.filter(Q(email=email) & ~Q(attendee__id=attendee.id)).exists():
                messages.error(request, 'Email already exists!')
                return redirect('edit_attendee_profile')

            attendee.user.email = email  # Save email in the user object
            attendee.user.save()
            attendee_form.save()
            return redirect('home')
    else:
        attendee_form = AttendeeForm2(instance=attendee)

    context = {
        'attendee_form': attendee_form
    }
    return render(request, 'app/update_attendee.html', context)


@login_required(login_url='login')
def OpenCameras(request):
    face_id = faceRecognition.recognizeFace()
    return redirect('home')


def scan_qr_code(request):
    users = User.objects.all()
    video_capture = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    # address = 'http://192.168.6.13:8080/video'
    # video_capture.open(address)
    error_sound_path = os.path.join(os.path.dirname(
        __file__), 'sounds', 'error_sound.mp3')
    success_sound_path = os.path.join(os.path.dirname(
        __file__), 'sounds', 'success_sound.mp3')

    while True:
        ret, frame = video_capture.read()

        if ret:
            qr_code_data = decode_qr_code(frame)

            if qr_code_data:
                qr_code_data = qr_code_data.decode("utf-8")
                for user in users:
                    if qr_code_data == str(user.username):
                        classroom = Classroom.objects.get(id=1)
                        attendee = user.attendee

                        # Check if the attendee belongs to the specified classroom
                        if not attendee.classrooms.filter(id=classroom.id).exists():
                            video_capture.release()
                            cv2.destroyAllWindows()
                            # Play error sounds
                            playsound.playsound(error_sound_path)
                            return render(request, 'app/invalid_qr_code.html')

                        attendance = Attendance.objects.filter(
                            classroom=classroom, attendee=attendee).first()

                        if attendance:
                            # Update existing attendance row
                            if not attendance.is_present:
                                attendance.is_present = True
                                attendance.check_in_time = datetime.now()
                                attendance.save()
                                video_capture.release()
                                cv2.destroyAllWindows()
                                # Play success sounds
                                playsound.playsound(success_sound_path)
                                return redirect('attendance-success')
                            else:
                                video_capture.release()
                                cv2.destroyAllWindows()
                                # Play success sounds
                                playsound.playsound(success_sound_path)
                                return render(request, 'app/attendance_exists.html')
                        else:
                            attendance = Attendance.objects.create(
                                classroom=classroom,
                                attendee=attendee,
                                is_present=True,
                                check_in_time=datetime.now()
                            )
                            attendance.save()
                            video_capture.release()
                            cv2.destroyAllWindows()
                            # Play success sounds
                            playsound.playsound(success_sound_path)
                            return redirect('attendance-success')

                # Invalid QR code, handle the case here
                video_capture.release()
                cv2.destroyAllWindows()
                playsound.playsound(error_sound_path)  # Play error sounds
                return render(request, 'app/invalid_qr_code.html')

            cv2.imshow('Scan QR Code', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    video_capture.release()
    cv2.destroyAllWindows()

    return render(request, 'app/scan_qr_code.html')


def attendance_success(request):
    return render(request, 'app/attendance_success.html')


def ListTrainer(request):
    if not request.user.is_staff and not request.user.is_superuser:
        # if user is not admin
        return HttpResponse(status=404)
    trainers = Trainer.objects.all()
    context = {'trainers': trainers}
    return render(request, 'app/list_trainer.html', context)


@login_required(login_url='login')
def ListTrainerClassroom(request):
    if not hasattr(request.user, 'trainer'):
        return HttpResponse(status=404)

    trainer_id = request.user.trainer.id
    s = request.GET.get('s', '')
    filter_option = request.GET.get('filter', '')

    classrooms = Classroom.objects.filter(trainer__id=trainer_id)

    q = request.GET.get('q', '')
    if q == '':
        attendances = Attendance.objects.filter(
            classroom__trainer__id=trainer_id)
    else:
        attendances = Attendance.objects.filter(
            Q(classroom__name=q) & Q(classroom__trainer__id=trainer_id))

    if request.method == "GET":
        attendances1 = Attendance.objects.filter(
            Q(attendee__name__icontains=s) & Q(classroom__trainer__id=trainer_id))

    if filter_option == 'present':
        attendances = attendances.filter(is_present=True)
    elif filter_option == 'absent':
        attendances = attendances.filter(is_present=False)

    present_count = attendances.filter(is_present=True).count()
    absent_count = attendances.filter(is_present=False).count()

    context = {
        'classrooms': classrooms,
        'attendances': attendances,
        'attendances1': attendances1,
        'present_count': present_count,
        'absent_count': absent_count
    }
    return render(request, 'app/list_attendance.html', context)
