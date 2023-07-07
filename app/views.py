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


def decode_qr_code(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    qr_codes = pyzbar.decode(gray)

    if qr_codes:
        return qr_codes[0].data

    return None

@login_required(login_url='login')
def AddClassroomPage(request):
    if not request.user.is_staff and not request.user.is_superuser:
        # if user is not admin
        return HttpResponse(status=404)
    classroom_form = ClassroomForm()
    return render(request, 'app/add_classroom.html', {'classroom_form': classroom_form})


@login_required(login_url='login')
def AddClassroom(request):
    if not request.user.is_staff and not request.user.is_superuser:
        # if user is not admin
        return HttpResponse(status=404)
    classroom_form = ClassroomForm()
    if request.method == 'POST':
        classroom_form = ClassroomForm(request.POST, request.FILES)
        if classroom_form.is_valid():
            classroom = classroom_form.save(commit=False)
            classroom.code = generate_random_string(8)
            classroom.save()
            subject = 'New Classroom assigned to you!'
            to_email = classroom.trainer.email
            from_email = settings.ADMIN_EMAIL
            email_template = 'app/new_classroom.html'
            context = {'classroom': classroom}
            email_content = render_to_string(email_template,context)
            email = EmailMessage(subject, email_content, from_email, [to_email])
            email.content_subtype = 'html'
            email.send()
            return redirect('list_classroom')
    return render(request, 'app/add_classroom.html', {'classroom_form': classroom_form})

@login_required(login_url='login')
def UpdateClassroom(request, pk):
    if not request.user.is_staff and not request.user.is_superuser:
        # if user is not admin
        return HttpResponse(status=404)
    classroom = Classroom.objects.get(id=pk)
    if request.method == 'POST':
        classroom_form = ClassroomForm(request.POST, request.FILES, instance=classroom)
        if classroom_form.is_valid():
            classroom_form.save()
            return redirect('list_classroom')
    else:
        classroom_form = ClassroomForm(instance=classroom)

    context = {
        'classroom_form': classroom_form
    }
    return render(request, 'app/update_classroom.html', context)

@login_required(login_url='login')
def DeleteClassroom(request, pk):
    if not request.user.is_staff and not request.user.is_superuser:
        # if user is not admin
        return HttpResponse(status=404)
    classroom = Classroom.objects.get(id=pk)
    if request.method == 'POST':
        classroom.delete()
        return redirect('list_classroom')
    context = {'classroom': classroom}
    return render(request, 'app/delete_classroom.html', context)

@login_required(login_url='login')
def ListClassroom(request):
    if not request.user.is_staff and not request.user.is_superuser:
        # if user is not admin
        return HttpResponse(status=404)
    classrooms = Classroom.objects.all()
    context = {'classrooms': classrooms}
    return render(request, 'app/list_classroom.html', context)

@login_required(login_url='login')
def TrainerClassrooms(request):
    if not hasattr(request.user, 'trainer'):
        # if user is not trainer
        return HttpResponse(status=404)
    classrooms = Classroom.objects.filter(trainer__id=request.user.trainer.id)
    error_message = None
    if request.method == "GET":
        search_query = request.GET.get('search', '')
        if search_query == '' or search_query.lower() == 'all':
            classrooms = Classroom.objects.filter(trainer__id=request.user.trainer.id)
        else:
            classrooms = Classroom.objects.filter(trainer__id=request.user.trainer.id,name__icontains=search_query)
        if len(classrooms) == 0:
            error_message = "No matching queries"
    context = {'classrooms': classrooms, 'error_message':error_message}
    return render(request, 'app/trainer_classrooms.html', context)

@login_required(login_url='login')
def classroom_info(request, pk):
    if not request.user.is_authenticated:
        return redirect('login')
    classroom = Classroom.objects.get(id=pk)
    resources = classroom.resources.all()
    user = request.user
    enrolled_classrooms = Classroom.objects.exclude(id=pk)
    students = len(classroom.attendees.all())
    error_message = None
    if students >= classroom.max_capacity:
        error_message = "You can't enroll! Students max capacity has already reached!"
    list_photos = ['jpg', 'jpeg', 'png', 'gif']
    context = {
        'classroom': classroom,
        'resources': resources,
        'classrooms': enrolled_classrooms,
        'list_photos': list_photos,
        'students': students,
        'error_message': error_message,
    }
    return render(request, 'app/course-single.html', context)

@login_required(login_url='login')
def AddToClassroom(request, classroom_id):
    if not hasattr(request.user, 'trainer'):
        # if user not trainer
        return HttpResponse(status=404)
    selected_classroom = Classroom.objects.get(id=classroom_id)
    classrooms = Classroom.objects.filter(trainer__id=request.user.trainer.id)
    # attendees bel selected_classroom.attendees.all() hiye bel 3ade attendee men doun s
    # bas la2enoo l classroom atribute li bel attendee model hiye manytomany
    attendees = selected_classroom.attendees.all()

    if request.method == 'POST':
        resource_form = ClassroomResourceForm(request.POST, request.FILES)
        if resource_form.is_valid():
            resource = resource_form.save(commit=False)
            resource.classroom = selected_classroom
            resource.save()
            messages.success(request, 'Resource uploaded successfully.')
            email_subject = 'Classrooms'
            email_body = f'new content for the classroom' + f"  {selected_classroom}"
            from_email = settings.ADMIN_EMAIL
            for attendee in attendees:
                to_email = [attendee.email, attendee.email]
                email = EmailMessage(email_subject, email_body, from_email, to_email)
                email.content_subtype = 'html'
                email.send()

            return redirect('course_single', classroom_id)

    else:
        resource_form = ClassroomResourceForm()

    context = {
        'resource_form': resource_form,
        'classrooms': classrooms,
        'selected_classroom': selected_classroom
    }
    return render(request, 'app/upload_resource.html', context)

@login_required(login_url='login')
def DeleteResources(request, pk):
    if not hasattr(request.user, 'trainer'):
        # if user is not trainer
        return HttpResponse(status=404)
    resource = ClassroomResource.objects.get(id=pk)
    classroom_id = resource.classroom.id
    if request.method == "POST":
        resource.delete()
        return redirect('course_single', classroom_id)
    context = {'resource': resource}
    return render(request, 'app/delete_resource.html', context)

@login_required(login_url='login')
def JoinClassroom(request):
    if not hasattr(request.user, 'attendee'):
        # if user is not student
        return HttpResponse(status=404)
    classrooms = Classroom.objects.all()
    error_message = None
    if request.method == "GET":
        search_query = request.GET.get('search', '')
        if search_query == '':
            classrooms = Classroom.objects.all()
        elif search_query.lower() == 'all':
            classrooms = Classroom.objects.all()
        else:
            classrooms = Classroom.objects.filter(name__icontains=search_query)
        if len(classrooms) == 0:
            error_message = "No matching queries!"

    context = {
        'classrooms': classrooms,
        'error_message': error_message,
    }
    return render(request, 'app/join_classroom.html', context)

@login_required(login_url='login')
def enroll_classroom(request, pk):
    if not hasattr(request.user, 'attendee'):
        # if user is not trainer
        return HttpResponse(status=404)
    classroom = Classroom.objects.get(id=pk)
    attendee = request.user.attendee
    error_message = None
    if attendee in classroom.attendees.all():
        return HttpResponse(status=404)
    if request.method == "POST":
        code = request.POST['code']
        if code != classroom.code:
            error_message = 'invalid code!!'
            # messages.error(request, 'invalid code!!')
            # return redirect('enroll', classroom.id)
            return render(request,'app/enroll_classroom.html',{'error_message': error_message})
        classroom.attendees.add(attendee)
        attendee_attendance = Attendance.objects.create(
            classroom=classroom,
            attendee=attendee,
            is_present=False,
            check_in_time=None
        )
        attendee_attendance.save()
        return redirect('course_single', classroom.id)
    context = {
        'classroom': classroom,
    }
    return render(request, 'app/enroll_classroom.html', context)

@login_required(login_url = 'login')
def unenroll_classroom(request, pk):
    if not hasattr(request.user, 'attendee'):
        # if user is not trainer
        return HttpResponse(status=404)
    classroom = Classroom.objects.get(id=pk)
    attendee = request.user.attendee
    if attendee not in classroom.attendees.all():
        return HttpResponse(status=404)
    if request.method == "POST":
        classroom.attendees.remove(attendee)
        attendance = Attendance.objects.get(classroom=classroom, attendee=attendee)
        attendance.delete()
        return redirect('course_single',classroom.id)
    context = {
        'classroom': classroom,
    }
    return render(request,'app/unenroll_classroom.html',context)